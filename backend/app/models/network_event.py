from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, ForeignKeyConstraint, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.base import Base
from backend.app.models.enums import NetworkEventSourceType
from backend.app.models.mixins import UUIDPrimaryKeyMixin


class NetworkEvent(Base, UUIDPrimaryKeyMixin):
    """Normalized network connection event (tenant- and site-scoped)."""

    __tablename__ = "network_events"
    __table_args__ = (
        UniqueConstraint(
            "sensor_id",
            "source_type",
            "source_event_id",
            name="uq_network_events_sensor_source",
        ),
        UniqueConstraint("id", "msp_id", name="uq_network_events_id_msp"),
        ForeignKeyConstraint(
            ["site_id", "msp_id"],
            ["sites.id", "sites.msp_id"],
            name="fk_network_events_site_msp",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["sensor_id", "site_id", "msp_id"],
            ["sensors.id", "sensors.site_id", "sensors.msp_id"],
            name="fk_network_events_sensor_site_msp",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["device_id", "msp_id", "site_id"],
            ["devices.id", "devices.msp_id", "devices.site_id"],
            name="fk_network_events_device_site_msp",
            ondelete="SET NULL",
        ),
    )

    msp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("msps.id", ondelete="CASCADE"),
        nullable=False,
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    sensor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sensors.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
    )

    source_type: Mapped[NetworkEventSourceType] = mapped_column(
        Enum(NetworkEventSourceType, name="network_event_source_type", native_enum=False),
        nullable=False,
    )
    source_event_id: Mapped[str] = mapped_column(String(128), nullable=False)

    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    src_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    dst_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transport_protocol: Mapped[str] = mapped_column(String(16), nullable=False)
    service: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    orig_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resp_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    orig_pkts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resp_pkts: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_record: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
