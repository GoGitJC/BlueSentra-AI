from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base
from backend.app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.customer import Customer
    from backend.app.models.user import User


class MSP(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "msps"
    __table_args__ = (UniqueConstraint("slug", name="uq_msps_slug"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    users: Mapped[list[User]] = relationship(back_populates="msp", cascade="all, delete-orphan")
    customers: Mapped[list[Customer]] = relationship(
        back_populates="msp",
        cascade="all, delete-orphan",
    )
