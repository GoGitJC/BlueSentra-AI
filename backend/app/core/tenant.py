"""Tenant scoping helpers for future authorization layers."""

from __future__ import annotations

import uuid
from typing import TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from backend.app.models.customer import Customer
from backend.app.models.device import Device
from backend.app.models.sensor import Sensor
from backend.app.models.site import Site
from backend.app.models.user import User

TenantScopedModel = TypeVar("TenantScopedModel", User, Customer, Site, Sensor, Device)


class TenantScopeError(ValueError):
    """Raised when a tenant-scoped operation is missing required context."""


def require_msp_id(msp_id: uuid.UUID | None) -> uuid.UUID:
    """Reject missing tenant IDs so queries cannot run unscoped by accident."""
    if msp_id is None:
        raise TenantScopeError("msp_id is required for tenant-scoped database access")
    return msp_id


def scope_to_msp(
    stmt: Select[tuple[TenantScopedModel]],
    model: type[TenantScopedModel],
    msp_id: uuid.UUID | None,
) -> Select[tuple[TenantScopedModel]]:
    """Restrict a SELECT to rows owned by the given MSP."""
    tenant_id = require_msp_id(msp_id)
    return stmt.where(model.msp_id == tenant_id)


def get_customer_for_msp(
    db: Session,
    *,
    msp_id: uuid.UUID | None,
    customer_id: uuid.UUID,
) -> Customer | None:
    tenant_id = require_msp_id(msp_id)
    return db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.msp_id == tenant_id,
        )
    )


def get_site_for_msp(
    db: Session,
    *,
    msp_id: uuid.UUID | None,
    site_id: uuid.UUID,
) -> Site | None:
    tenant_id = require_msp_id(msp_id)
    return db.scalar(
        select(Site).where(
            Site.id == site_id,
            Site.msp_id == tenant_id,
        )
    )


def get_sensor_for_msp(
    db: Session,
    *,
    msp_id: uuid.UUID | None,
    sensor_id: uuid.UUID,
) -> Sensor | None:
    tenant_id = require_msp_id(msp_id)
    return db.scalar(
        select(Sensor).where(
            Sensor.id == sensor_id,
            Sensor.msp_id == tenant_id,
        )
    )


def get_device_for_msp(
    db: Session,
    *,
    msp_id: uuid.UUID | None,
    device_id: uuid.UUID,
) -> Device | None:
    tenant_id = require_msp_id(msp_id)
    return db.scalar(
        select(Device).where(
            Device.id == device_id,
            Device.msp_id == tenant_id,
        )
    )
