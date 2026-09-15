"""Create and query MSP tenant hierarchy (no authentication yet)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.customer import Customer
from backend.app.models.device import Device
from backend.app.models.enums import SensorStatus, UserRole
from backend.app.models.msp import MSP
from backend.app.models.sensor import Sensor
from backend.app.models.site import Site
from backend.app.models.user import User


class TenantHierarchyError(ValueError):
    pass


def _persist(db: Session, entity: MSP | User | Customer | Site | Sensor | Device):
    db.add(entity)
    db.flush()
    db.refresh(entity)
    return entity


def create_msp(
    db: Session,
    *,
    name: str,
    slug: str,
) -> MSP:
    return _persist(db, MSP(name=name, slug=slug))


def create_user(
    db: Session,
    *,
    msp_id: uuid.UUID,
    email: str,
    full_name: str | None = None,
    role: UserRole = UserRole.ANALYST,
) -> User:
    return _persist(
        db,
        User(
            msp_id=msp_id,
            email=email.lower().strip(),
            full_name=full_name,
            role=role,
        ),
    )


def create_customer(
    db: Session,
    *,
    msp_id: uuid.UUID,
    name: str,
    slug: str,
) -> Customer:
    return _persist(db, Customer(msp_id=msp_id, name=name, slug=slug))


def create_site(
    db: Session,
    *,
    msp_id: uuid.UUID,
    customer_id: uuid.UUID,
    name: str,
    slug: str,
    timezone: str = "UTC",
) -> Site:
    customer = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.msp_id == msp_id,
        )
    )
    if customer is None:
        raise TenantHierarchyError("Customer not found for this MSP")

    site = Site(
        msp_id=msp_id,
        customer_id=customer_id,
        name=name,
        slug=slug,
        timezone=timezone,
    )
    try:
        return _persist(db, site)
    except IntegrityError as exc:
        raise TenantHierarchyError("Invalid site tenant relationship") from exc


def create_sensor(
    db: Session,
    *,
    msp_id: uuid.UUID,
    site_id: uuid.UUID,
    name: str,
    slug: str,
    status: SensorStatus = SensorStatus.PENDING,
) -> Sensor:
    site = db.scalar(
        select(Site).where(Site.id == site_id, Site.msp_id == msp_id)
    )
    if site is None:
        raise TenantHierarchyError("Site not found for this MSP")

    return _persist(
        db,
        Sensor(
            msp_id=msp_id,
            site_id=site_id,
            name=name,
            slug=slug,
            status=status,
        ),
    )


def create_device(
    db: Session,
    *,
    msp_id: uuid.UUID,
    site_id: uuid.UUID,
    mac_address: str | None = None,
    ip_address: str | None = None,
    hostname: str | None = None,
    device_type: str | None = None,
) -> Device:
    site = db.scalar(
        select(Site).where(Site.id == site_id, Site.msp_id == msp_id)
    )
    if site is None:
        raise TenantHierarchyError("Site not found for this MSP")

    return _persist(
        db,
        Device(
            msp_id=msp_id,
            site_id=site_id,
            mac_address=mac_address,
            ip_address=ip_address,
            hostname=hostname,
            device_type=device_type,
        ),
    )


def list_customers_for_msp(db: Session, msp_id: uuid.UUID) -> list[Customer]:
    return list(
        db.scalars(select(Customer).where(Customer.msp_id == msp_id).order_by(Customer.name))
    )
