"""Read-only PostgreSQL queries for the local Network Events dashboard viewer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.app.models.customer import Customer
from backend.app.models.network_event import NetworkEvent
from backend.app.models.sensor import Sensor
from backend.app.models.site import Site


class ViewerConfigError(ValueError):
    """Local viewer configuration is missing or invalid."""


@dataclass(frozen=True)
class TenantOption:
    id: uuid.UUID
    label: str


@dataclass(frozen=True)
class EventRow:
    id: uuid.UUID
    event_at: datetime
    sensor_name: str
    src_ip: str
    src_port: int | None
    dst_ip: str
    dst_port: int | None
    transport_protocol: str
    service: str | None
    orig_bytes: int | None
    resp_bytes: int | None
    duration: float | None


@dataclass(frozen=True)
class EventSummary:
    connection_count: int
    distinct_src_ip_count: int
    total_orig_bytes: int | None
    total_resp_bytes: int | None


@dataclass(frozen=True)
class EventQueryResult:
    rows: list[EventRow]
    total_matching: int


@dataclass(frozen=True)
class EventTimeBounds:
    earliest: datetime | None
    latest: datetime | None


@dataclass(frozen=True)
class EventDetail:
    id: uuid.UUID
    event_at: datetime
    site_name: str
    sensor_name: str
    source_type: str
    source_event_id: str
    src_ip: str
    src_port: int | None
    dst_ip: str
    dst_port: int | None
    transport_protocol: str
    service: str | None
    orig_bytes: int | None
    resp_bytes: int | None
    orig_pkts: int | None
    resp_pkts: int | None
    duration: float | None
    source_record: dict


@dataclass(frozen=True)
class EventViewFilters:
    customer_id: uuid.UUID | None = None
    site_id: uuid.UUID | None = None
    sensor_id: uuid.UUID | None = None
    start_utc: datetime | None = None
    end_utc: datetime | None = None


def require_viewer_msp_id(raw: str | None) -> uuid.UUID:
    if raw is None or not str(raw).strip():
        raise ViewerConfigError(
            "BLUESENTRA_VIEWER_MSP_ID must be set to a valid MSP UUID for the Network Events viewer."
        )
    try:
        return uuid.UUID(str(raw).strip())
    except ValueError as exc:
        raise ViewerConfigError(
            "BLUESENTRA_VIEWER_MSP_ID must be a valid UUID."
        ) from exc


def validate_filter_ownership(
    db: Session,
    *,
    msp_id: uuid.UUID,
    filters: EventViewFilters,
) -> None:
    if filters.customer_id is not None:
        customer = db.scalar(
            select(Customer).where(
                Customer.id == filters.customer_id,
                Customer.msp_id == msp_id,
            )
        )
        if customer is None:
            raise ViewerConfigError("Selected customer is not owned by the configured MSP.")

    if filters.site_id is not None:
        site = db.scalar(
            select(Site).where(
                Site.id == filters.site_id,
                Site.msp_id == msp_id,
            )
        )
        if site is None:
            raise ViewerConfigError("Selected site is not owned by the configured MSP.")
        if filters.customer_id is not None and site.customer_id != filters.customer_id:
            raise ViewerConfigError("Selected site does not belong to the selected customer.")

    if filters.sensor_id is not None:
        sensor = db.scalar(
            select(Sensor).where(
                Sensor.id == filters.sensor_id,
                Sensor.msp_id == msp_id,
            )
        )
        if sensor is None:
            raise ViewerConfigError("Selected sensor is not owned by the configured MSP.")
        if filters.site_id is not None and sensor.site_id != filters.site_id:
            raise ViewerConfigError("Selected sensor does not belong to the selected site.")


def _base_event_query(
    msp_id: uuid.UUID,
    filters: EventViewFilters,
) -> Select[tuple[NetworkEvent, str]]:
    stmt = (
        select(NetworkEvent, Sensor.name)
        .join(Sensor, NetworkEvent.sensor_id == Sensor.id)
        .where(NetworkEvent.msp_id == msp_id)
    )
    if filters.customer_id is not None:
        stmt = stmt.join(Site, NetworkEvent.site_id == Site.id).where(
            Site.customer_id == filters.customer_id
        )
    if filters.site_id is not None:
        stmt = stmt.where(NetworkEvent.site_id == filters.site_id)
    if filters.sensor_id is not None:
        stmt = stmt.where(NetworkEvent.sensor_id == filters.sensor_id)
    if filters.start_utc is not None:
        stmt = stmt.where(NetworkEvent.event_at >= filters.start_utc)
    if filters.end_utc is not None:
        stmt = stmt.where(NetworkEvent.event_at <= filters.end_utc)
    return stmt


def msp_event_count(db: Session, *, msp_id: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(NetworkEvent).where(NetworkEvent.msp_id == msp_id)
        )
        or 0
    )


def get_event_time_bounds(db: Session, *, msp_id: uuid.UUID) -> EventTimeBounds:
    earliest = db.scalar(
        select(func.min(NetworkEvent.event_at)).where(NetworkEvent.msp_id == msp_id)
    )
    latest = db.scalar(
        select(func.max(NetworkEvent.event_at)).where(NetworkEvent.msp_id == msp_id)
    )
    return EventTimeBounds(earliest=earliest, latest=latest)


def default_time_window(bounds: EventTimeBounds) -> tuple[datetime, datetime]:
    """Window ending at latest MSP event (30-day lookback or earliest event)."""
    if bounds.latest is None:
        now = datetime.now(tz=UTC)
        return now - timedelta(days=30), now
    end = bounds.latest
    if bounds.earliest is None:
        return end - timedelta(days=30), end
    start = max(bounds.earliest, end - timedelta(days=30))
    return start, end


def list_customers(db: Session, *, msp_id: uuid.UUID) -> list[TenantOption]:
    rows = db.scalars(
        select(Customer)
        .where(Customer.msp_id == msp_id)
        .order_by(Customer.name)
    ).all()
    return [TenantOption(id=r.id, label=r.name) for r in rows]


def list_sites(
    db: Session,
    *,
    msp_id: uuid.UUID,
    customer_id: uuid.UUID | None,
) -> list[TenantOption]:
    stmt = select(Site).where(Site.msp_id == msp_id)
    if customer_id is not None:
        stmt = stmt.where(Site.customer_id == customer_id)
    rows = db.scalars(stmt.order_by(Site.name)).all()
    return [TenantOption(id=r.id, label=r.name) for r in rows]


def list_sensors(
    db: Session,
    *,
    msp_id: uuid.UUID,
    site_id: uuid.UUID | None,
) -> list[TenantOption]:
    stmt = select(Sensor).where(Sensor.msp_id == msp_id)
    if site_id is not None:
        stmt = stmt.where(Sensor.site_id == site_id)
    rows = db.scalars(stmt.order_by(Sensor.name)).all()
    return [TenantOption(id=r.id, label=f"{r.name} ({r.slug})") for r in rows]


def query_events_page(
    db: Session,
    *,
    msp_id: uuid.UUID,
    filters: EventViewFilters,
    page: int,
    page_size: int,
) -> EventQueryResult:
    validate_filter_ownership(db, msp_id=msp_id, filters=filters)
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 25

    base = _base_event_query(msp_id, filters)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    offset = (page - 1) * page_size
    rows = db.execute(
        base.order_by(NetworkEvent.event_at.desc(), NetworkEvent.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    event_rows = [
        EventRow(
            id=event.id,
            event_at=event.event_at,
            sensor_name=sensor_name,
            src_ip=event.src_ip,
            src_port=event.src_port,
            dst_ip=event.dst_ip,
            dst_port=event.dst_port,
            transport_protocol=event.transport_protocol,
            service=event.service,
            orig_bytes=event.orig_bytes,
            resp_bytes=event.resp_bytes,
            duration=event.duration,
        )
        for event, sensor_name in rows
    ]
    return EventQueryResult(rows=event_rows, total_matching=total)


def summarize_events(
    db: Session,
    *,
    msp_id: uuid.UUID,
    filters: EventViewFilters,
) -> EventSummary:
    validate_filter_ownership(db, msp_id=msp_id, filters=filters)
    base = _base_event_query(msp_id, filters).subquery()
    row = db.execute(
        select(
            func.count(),
            func.count(func.distinct(base.c.src_ip)),
            func.sum(base.c.orig_bytes),
            func.sum(base.c.resp_bytes),
        ).select_from(base)
    ).one()

    return EventSummary(
        connection_count=int(row[0] or 0),
        distinct_src_ip_count=int(row[1] or 0),
        total_orig_bytes=int(row[2]) if row[2] is not None else None,
        total_resp_bytes=int(row[3]) if row[3] is not None else None,
    )


def _event_matches_filters(
    event: NetworkEvent,
    *,
    filters: EventViewFilters,
    site_customer_id: uuid.UUID,
) -> bool:
    if filters.customer_id is not None and site_customer_id != filters.customer_id:
        return False
    if filters.site_id is not None and event.site_id != filters.site_id:
        return False
    if filters.sensor_id is not None and event.sensor_id != filters.sensor_id:
        return False
    if filters.start_utc is not None and event.event_at < filters.start_utc:
        return False
    if filters.end_utc is not None and event.event_at > filters.end_utc:
        return False
    return True


def get_event_detail(
    db: Session,
    *,
    msp_id: uuid.UUID,
    event_id: uuid.UUID,
    filters: EventViewFilters,
) -> EventDetail | None:
    """Load one event for the viewer; None if missing, wrong MSP, or outside filters."""
    validate_filter_ownership(db, msp_id=msp_id, filters=filters)
    row = db.execute(
        select(NetworkEvent, Sensor.name, Site.name, Site.customer_id)
        .join(Sensor, NetworkEvent.sensor_id == Sensor.id)
        .join(Site, NetworkEvent.site_id == Site.id)
        .where(NetworkEvent.id == event_id, NetworkEvent.msp_id == msp_id)
    ).one_or_none()
    if row is None:
        return None
    event, sensor_name, site_name, site_customer_id = row
    if not _event_matches_filters(
        event, filters=filters, site_customer_id=site_customer_id
    ):
        return None
    return EventDetail(
        id=event.id,
        event_at=event.event_at,
        site_name=site_name,
        sensor_name=sensor_name,
        source_type=event.source_type.value,
        source_event_id=event.source_event_id,
        src_ip=event.src_ip,
        src_port=event.src_port,
        dst_ip=event.dst_ip,
        dst_port=event.dst_port,
        transport_protocol=event.transport_protocol,
        service=event.service,
        orig_bytes=event.orig_bytes,
        resp_bytes=event.resp_bytes,
        orig_pkts=event.orig_pkts,
        resp_pkts=event.resp_pkts,
        duration=event.duration,
        source_record=dict(event.source_record),
    )
