import uuid

import pytest

from backend.app.core.tenant import (
    TenantScopeError,
    get_customer_for_msp,
    get_device_for_msp,
    get_sensor_for_msp,
    get_site_for_msp,
    require_msp_id,
    scope_to_msp,
)
from backend.app.models.customer import Customer
from backend.app.services import tenant_hierarchy as th
from sqlalchemy import select


def test_require_msp_id_rejects_none():
    with pytest.raises(TenantScopeError):
        require_msp_id(None)


def test_scope_to_msp_rejects_none():
    with pytest.raises(TenantScopeError):
        scope_to_msp(select(Customer), Customer, None)


def test_scoped_lookups_do_not_cross_msps(db_session):
    msp_a = th.create_msp(db_session, name="Scope A", slug="scope-a")
    msp_b = th.create_msp(db_session, name="Scope B", slug="scope-b")
    customer = th.create_customer(
        db_session,
        msp_id=msp_a.id,
        name="Scoped Customer",
        slug="scoped-customer",
    )
    site = th.create_site(
        db_session,
        msp_id=msp_a.id,
        customer_id=customer.id,
        name="Scoped Site",
        slug="scoped-site",
    )
    sensor = th.create_sensor(
        db_session,
        msp_id=msp_a.id,
        site_id=site.id,
        name="Scoped Sensor",
        slug="scoped-sensor",
    )
    device = th.create_device(
        db_session,
        msp_id=msp_a.id,
        site_id=site.id,
        mac_address="de:ad:be:ef:00:01",
        device_type="printer",
    )

    wrong_msp = msp_b.id
    assert get_customer_for_msp(
        db_session, msp_id=wrong_msp, customer_id=customer.id
    ) is None
    assert get_site_for_msp(db_session, msp_id=wrong_msp, site_id=site.id) is None
    assert get_sensor_for_msp(db_session, msp_id=wrong_msp, sensor_id=sensor.id) is None
    assert get_device_for_msp(db_session, msp_id=wrong_msp, device_id=device.id) is None

    assert get_customer_for_msp(
        db_session, msp_id=msp_a.id, customer_id=customer.id
    ) is not None


def test_scoped_lookups_reject_none_msp_id():
    class _UnusedSession:
        pass

    with pytest.raises(TenantScopeError):
        get_site_for_msp(_UnusedSession(), msp_id=None, site_id=uuid.uuid4())
