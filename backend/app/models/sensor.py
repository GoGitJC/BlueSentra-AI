from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base
from backend.app.models.enums import SensorStatus
from backend.app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.site import Site


class Sensor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sensors"
    __table_args__ = (
        UniqueConstraint("site_id", "slug", name="uq_sensors_site_slug"),
        ForeignKeyConstraint(
            ["site_id", "msp_id"],
            ["sites.id", "sites.msp_id"],
            name="fk_sensors_site_msp",
            ondelete="CASCADE",
        ),
    )

    msp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("msps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[SensorStatus] = mapped_column(
        Enum(SensorStatus, name="sensor_status", native_enum=False),
        nullable=False,
        default=SensorStatus.PENDING,
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    site: Mapped[Site] = relationship(
        back_populates="sensors",
        foreign_keys=[site_id],
    )
