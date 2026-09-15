from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base
from backend.app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.msp import MSP
    from backend.app.models.site import Site


class Customer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("msp_id", "slug", name="uq_customers_msp_slug"),
        UniqueConstraint("id", "msp_id", name="uq_customers_id_msp"),
    )

    msp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("msps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)

    msp: Mapped[MSP] = relationship(back_populates="customers")
    sites: Mapped[list[Site]] = relationship(
        back_populates="customer",
        foreign_keys="Site.customer_id",
        cascade="all, delete-orphan",
    )
