import uuid
from datetime import UTC, datetime

import pytest

from backend.app.models.enums import NetworkEventSourceType
from backend.app.models.network_event import NetworkEvent
from backend.app.services import tenant_hierarchy as th
from backend.app.services.network_events_view import (
    EventViewFilters,
    ViewerConfigError,
    default_time_window,
    get_event_detail,
    list_sites,
    query_events_page,
    require_viewer_msp_id,
    summarize_events,
    validate_filter_ownership,
)


def test_require_viewer_msp_id_fail_closed():
    with pytest.raises(ViewerConfigError):
        require_viewer_msp_id(None)
    with pytest.raises(ViewerConfigError):
        require_viewer_msp_id("not-a-uuid")


def test_require_viewer_msp_id_accepts_uuid():
    value = uuid.uuid4()
    assert require_viewer_msp_id(str(value)) == value


def test_list_sites_scoped_to_msp(db_session):
    msp_a = th.create_msp(db_session, name="A", slug=f"msp-nev-a-{uuid.uuid4().hex[:6]}")
    msp_b = th.create_msp(db_session, name="B", slug=f"msp-nev-b-{uuid.uuid4().hex[:6]}")
    cust_a = th.create_customer(db_session, msp_id=msp_a.id, name="CA", slug=f"c-a-{uuid.uuid4().hex[:6]}")
    th.create_site(
        db_session,
        msp_id=msp_a.id,
        customer_id=cust_a.id,
        name="Site A",
        slug=f"s-a-{uuid.uuid4().hex[:6]}",
    )
    sites_b = list_sites(db_session, msp_id=msp_b.id, customer_id=None)
    assert sites_b == []


def test_validate_filter_rejects_cross_customer_site(db_session):
    msp = th.create_msp(db_session, name="M", slug=f"msp-nev-{uuid.uuid4().hex[:6]}")
    c1 = th.create_customer(db_session, msp_id=msp.id, name="C1", slug=f"c1-{uuid.uuid4().hex[:6]}")
    c2 = th.create_customer(db_session, msp_id=msp.id, name="C2", slug=f"c2-{uuid.uuid4().hex[:6]}")
    site2 = th.create_site(
        db_session,
        msp_id=msp.id,
        customer_id=c2.id,
        name="S2",
        slug=f"s2-{uuid.uuid4().hex[:6]}",
    )
    with pytest.raises(ViewerConfigError):
        validate_filter_ownership(
            db_session,
            msp_id=msp.id,
            filters=EventViewFilters(customer_id=c1.id, site_id=site2.id),
        )


def test_query_events_pagination_and_order(db_session):
    slug = uuid.uuid4().hex[:8]
    msp = th.create_msp(db_session, name="M", slug=f"msp-pg-{slug}")
    cust = th.create_customer(db_session, msp_id=msp.id, name="C", slug=f"c-{slug}")
    site = th.create_site(
        db_session,
        msp_id=msp.id,
        customer_id=cust.id,
        name="S",
        slug=f"s-{slug}",
    )
    sensor = th.create_sensor(
        db_session,
        msp_id=msp.id,
        site_id=site.id,
        name="Sensor",
        slug=f"sen-{slug}",
    )
    for idx in range(5):
        db_session.add(
            NetworkEvent(
                msp_id=msp.id,
                site_id=site.id,
                sensor_id=sensor.id,
                source_type=NetworkEventSourceType.ZEEK_CONN,
                source_event_id=f"UID-{idx}",
                event_at=datetime(2024, 1, 1, 0, idx, tzinfo=UTC),
                src_ip=f"192.0.2.{idx + 1}",
                dst_ip="198.51.100.1",
                src_port=1000 + idx,
                dst_port=443,
                transport_protocol="tcp",
                orig_bytes=100 * (idx + 1) if idx % 2 == 0 else None,
                resp_bytes=200 if idx == 0 else None,
                source_record={"uid": f"UID-{idx}"},
            )
        )
    db_session.flush()

    filters = EventViewFilters(
        sensor_id=sensor.id,
        start_utc=datetime(2024, 1, 1, tzinfo=UTC),
        end_utc=datetime(2024, 1, 2, tzinfo=UTC),
    )
    page1 = query_events_page(
        db_session, msp_id=msp.id, filters=filters, page=1, page_size=2
    )
    page2 = query_events_page(
        db_session, msp_id=msp.id, filters=filters, page=2, page_size=2
    )
    assert page1.total_matching == 5
    assert len(page1.rows) == 2
    assert len(page2.rows) == 2
    assert page1.rows[0].event_at >= page1.rows[1].event_at

    summary = summarize_events(db_session, msp_id=msp.id, filters=filters)
    assert summary.connection_count == 5
    assert summary.distinct_src_ip_count == 5
    assert summary.total_orig_bytes == 100 + 300 + 500


def test_default_time_window_ends_at_latest():
    latest = datetime(2024, 6, 1, 12, 0, tzinfo=UTC)
    earliest = datetime(2024, 5, 1, tzinfo=UTC)
    start, end = default_time_window(
        type("B", (), {"earliest": earliest, "latest": latest})()
    )
    assert end == latest
    assert start <= end


def test_get_event_detail_scoped_to_msp_and_filters(db_session):
    slug = uuid.uuid4().hex[:8]
    msp_a = th.create_msp(db_session, name="A", slug=f"msp-det-a-{slug}")
    msp_b = th.create_msp(db_session, name="B", slug=f"msp-det-b-{slug}")
    cust = th.create_customer(db_session, msp_id=msp_a.id, name="C", slug=f"c-{slug}")
    site = th.create_site(
        db_session,
        msp_id=msp_a.id,
        customer_id=cust.id,
        name="S",
        slug=f"s-{slug}",
    )
    sensor = th.create_sensor(
        db_session,
        msp_id=msp_a.id,
        site_id=site.id,
        name="Sensor",
        slug=f"sen-{slug}",
    )
    event = NetworkEvent(
        msp_id=msp_a.id,
        site_id=site.id,
        sensor_id=sensor.id,
        source_type=NetworkEventSourceType.ZEEK_CONN,
        source_event_id=f"UID-{slug}",
        event_at=datetime(2024, 3, 1, 12, 0, tzinfo=UTC),
        src_ip="192.0.2.10",
        dst_ip="198.51.100.5",
        src_port=4444,
        dst_port=443,
        transport_protocol="tcp",
        service="ssl",
        orig_bytes=1000,
        resp_bytes=2000,
        orig_pkts=10,
        resp_pkts=8,
        duration=1.5,
        source_record={"uid": f"UID-{slug}"},
    )
    db_session.add(event)
    db_session.flush()

    filters = EventViewFilters(
        sensor_id=sensor.id,
        start_utc=datetime(2024, 3, 1, tzinfo=UTC),
        end_utc=datetime(2024, 3, 2, tzinfo=UTC),
    )
    detail = get_event_detail(
        db_session, msp_id=msp_a.id, event_id=event.id, filters=filters
    )
    assert detail is not None
    assert detail.src_ip == "192.0.2.10"
    assert detail.site_name == "S"
    assert detail.source_record["uid"] == f"UID-{slug}"

    assert get_event_detail(
        db_session,
        msp_id=msp_b.id,
        event_id=event.id,
        filters=EventViewFilters(),
    ) is None

    narrow = EventViewFilters(
        sensor_id=sensor.id,
        start_utc=datetime(2024, 4, 1, tzinfo=UTC),
        end_utc=datetime(2024, 4, 2, tzinfo=UTC),
    )
    assert get_event_detail(
        db_session, msp_id=msp_a.id, event_id=event.id, filters=narrow
    ) is None
