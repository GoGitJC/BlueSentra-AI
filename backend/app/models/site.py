from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base
from backend.app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.customer import Customer
    from backend.app.models.device import Device
    from backend.app.models.sensor import Sensor


class Site(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sites"
    __table_args__ = (
        UniqueConstraint("customer_id", "slug", name="uq_sites_customer_slug"),
        UniqueConstraint("id", "msp_id", name="uq_sites_id_msp"),
        ForeignKeyConstraint(
            ["customer_id", "msp_id"],
            ["customers.id", "customers.msp_id"],
            name="fk_sites_customer_msp",
            ondelete="CASCADE",
        ),
    )

    msp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("msps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")

    customer: Mapped[Customer] = relationship(
        back_populates="sites",
        foreign_keys=[customer_id],
    )
    sensors: Mapped[list[Sensor]] = relationship(
        back_populates="site",
        foreign_keys="Sensor.site_id",
        cascade="all, delete-orphan",
    )
    devices: Mapped[list[Device]] = relationship(
        back_populates="site",
        foreign_keys="Device.site_id",
        cascade="all, delete-orphan",
    )
