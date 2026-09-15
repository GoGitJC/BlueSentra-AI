import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.core.tenant import get_customer_for_msp, scope_to_msp
from backend.app.models.customer import Customer
from backend.app.models.device import Device
from backend.app.models.enums import SensorStatus, UserRole
from backend.app.models.sensor import Sensor
from backend.app.models.site import Site
from backend.app.services import tenant_hierarchy as th
from sqlalchemy import select


def test_msp_hierarchy_creation(db_session):
    msp_a = th.create_msp(db_session, name="MSP A", slug="msp-a")
    msp_b = th.create_msp(db_session, name="MSP B", slug="msp-b")

    th.create_user(
        db_session,
        msp_id=msp_a.id,
        email="analyst@mspa.example",
        role=UserRole.ANALYST,
    )
    customer_a = th.create_customer(
        db_session,
        msp_id=msp_a.id,
        name="Customer A",
        slug="customer-a",
    )
    site_a = th.create_site(
        db_session,
        msp_id=msp_a.id,
        customer_id=customer_a.id,
        name="Site A",
        slug="site-a",
    )
    sensor = th.create_sensor(
        db_session,
        msp_id=msp_a.id,
        site_id=site_a.id,
        name="Sensor 1",
        slug="sensor-1",
    )
    device = th.create_device(
        db_session,
        msp_id=msp_a.id,
        site_id=site_a.id,
        mac_address="aa:bb:cc:dd:ee:ff",
        device_type="camera",
    )

    assert sensor.msp_id == msp_a.id
    assert device.msp_id == msp_a.id

    scoped = db_session.scalars(
        scope_to_msp(select(Customer), Customer, msp_a.id)
    ).all()
    assert len(scoped) == 1
    assert scoped[0].id == customer_a.id

    assert get_customer_for_msp(
        db_session, msp_id=msp_b.id, customer_id=customer_a.id
    ) is None


def test_helper_rejects_customer_from_other_msp(db_session):
    msp_a = th.create_msp(db_session, name="MSP A", slug="msp-a-helper")
    msp_b = th.create_msp(db_session, name="MSP B", slug="msp-b-helper")
    customer_b = th.create_customer(
        db_session,
        msp_id=msp_b.id,
        name="Customer B",
        slug="customer-b-helper",
    )

    with pytest.raises(th.TenantHierarchyError):
        th.create_site(
            db_session,
            msp_id=msp_a.id,
            customer_id=customer_b.id,
            name="Bad Site",
            slug="bad-site-helper",
        )


def test_helper_rejects_site_from_other_msp_for_sensor(db_session):
    msp_a = th.create_msp(db_session, name="MSP A", slug="msp-a-sensor-helper")
    msp_b = th.create_msp(db_session, name="MSP B", slug="msp-b-sensor-helper")
    customer_b = th.create_customer(
        db_session,
        msp_id=msp_b.id,
        name="Customer B",
        slug="customer-b-sensor",
    )
    site_b = th.create_site(
        db_session,
        msp_id=msp_b.id,
        customer_id=customer_b.id,
        name="Site B",
        slug="site-b-sensor",
    )

    with pytest.raises(th.TenantHierarchyError):
        th.create_sensor(
            db_session,
            msp_id=msp_a.id,
            site_id=site_b.id,
            name="Bad Sensor",
            slug="bad-sensor",
        )


def test_helper_rejects_site_from_other_msp_for_device(db_session):
    msp_a = th.create_msp(db_session, name="MSP A", slug="msp-a-device-helper")
    msp_b = th.create_msp(db_session, name="MSP B", slug="msp-b-device-helper")
    customer_b = th.create_customer(
        db_session,
        msp_id=msp_b.id,
        name="Customer B",
        slug="customer-b-device",
    )
    site_b = th.create_site(
        db_session,
        msp_id=msp_b.id,
        customer_id=customer_b.id,
        name="Site B",
        slug="site-b-device",
    )

    with pytest.raises(th.TenantHierarchyError):
        th.create_device(
            db_session,
            msp_id=msp_a.id,
            site_id=site_b.id,
            mac_address="11:22:33:44:55:66",
        )


def test_db_rejects_site_with_customer_from_other_msp(db_session):
    msp_a = th.create_msp(db_session, name="MSP A", slug="msp-a-2")
    msp_b = th.create_msp(db_session, name="MSP B", slug="msp-b-2")
    customer_b = th.create_customer(
        db_session,
        msp_id=msp_b.id,
        name="Customer B",
        slug="customer-b",
    )

    site = Site(
        msp_id=msp_a.id,
        customer_id=customer_b.id,
        name="Bad Site",
        slug="bad-site",
    )
    db_session.add(site)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_db_rejects_sensor_with_site_from_other_msp(db_session):
    msp_a = th.create_msp(db_session, name="MSP A", slug="msp-a-sensor-db")
    msp_b = th.create_msp(db_session, name="MSP B", slug="msp-b-sensor-db")
    customer_b = th.create_customer(
        db_session,
        msp_id=msp_b.id,
        name="Customer B",
        slug="customer-b-sensor-db",
    )
    site_b = th.create_site(
        db_session,
        msp_id=msp_b.id,
        customer_id=customer_b.id,
        name="Site B",
        slug="site-b-sensor-db",
    )

    sensor = Sensor(
        msp_id=msp_a.id,
        site_id=site_b.id,
        name="Bad Sensor",
        slug="bad-sensor-db",
        status=SensorStatus.PENDING,
    )
    db_session.add(sensor)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_db_rejects_device_with_site_from_other_msp(db_session):
    msp_a = th.create_msp(db_session, name="MSP A", slug="msp-a-device-db")
    msp_b = th.create_msp(db_session, name="MSP B", slug="msp-b-device-db")
    customer_b = th.create_customer(
        db_session,
        msp_id=msp_b.id,
        name="Customer B",
        slug="customer-b-device-db",
    )
    site_b = th.create_site(
        db_session,
        msp_id=msp_b.id,
        customer_id=customer_b.id,
        name="Site B",
        slug="site-b-device-db",
    )

    device = Device(
        msp_id=msp_a.id,
        site_id=site_b.id,
        mac_address="22:33:44:55:66:77",
    )
    db_session.add(device)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_device_creation_requires_valid_site(db_session):
    msp = th.create_msp(db_session, name="MSP Solo", slug="msp-solo")
    with pytest.raises(th.TenantHierarchyError):
        th.create_device(
            db_session,
            msp_id=msp.id,
            site_id=uuid.uuid4(),
            mac_address="11:22:33:44:55:66",
        )
