import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from backend.app.models.enums import NetworkEventSourceType
from backend.app.models.network_event import NetworkEvent
from backend.app.services import tenant_hierarchy as th
from backend.app.services.zeek_conn_import import (
    ImportValidationError,
    import_zeek_conn_file,
    resolve_sensor_for_import,
)

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "zeek" / "conn_sample.jsonl"


def _build_site(db_session, *, slug_prefix: str):
    msp = th.create_msp(db_session, name=f"MSP {slug_prefix}", slug=f"msp-{slug_prefix}")
    customer = th.create_customer(
        db_session,
        msp_id=msp.id,
        name="Customer",
        slug=f"cust-{slug_prefix}",
    )
    site = th.create_site(
        db_session,
        msp_id=msp.id,
        customer_id=customer.id,
        name="Site",
        slug=f"site-{slug_prefix}",
    )
    sensor = th.create_sensor(
        db_session,
        msp_id=msp.id,
        site_id=site.id,
        name="Sensor",
        slug=f"sensor-{slug_prefix}",
    )
    return msp, site, sensor


def test_import_counts_and_reimport_is_idempotent(db_session):
    msp, _site, sensor = _build_site(db_session, slug_prefix="import-a")

    first = import_zeek_conn_file(
        db_session,
        msp_id=msp.id,
        sensor_id=sensor.id,
        file_path=FIXTURE_PATH,
    )
    assert first.inserted == 3
    assert first.duplicates == 0
    assert first.rejected_count == 0

    second = import_zeek_conn_file(
        db_session,
        msp_id=msp.id,
        sensor_id=sensor.id,
        file_path=FIXTURE_PATH,
    )
    assert second.inserted == 0
    assert second.duplicates == 3
    assert second.rejected_count == 0

    total = db_session.scalar(select(func.count()).select_from(NetworkEvent))
    assert total == 3


def test_same_fixture_different_sensors_inserts_independently(db_session):
    msp, site, sensor_a = _build_site(db_session, slug_prefix="import-b")
    sensor_b = th.create_sensor(
        db_session,
        msp_id=msp.id,
        site_id=site.id,
        name="Sensor B",
        slug="sensor-b-import",
    )

    result_a = import_zeek_conn_file(
        db_session,
        msp_id=msp.id,
        sensor_id=sensor_a.id,
        file_path=FIXTURE_PATH,
    )
    result_b = import_zeek_conn_file(
        db_session,
        msp_id=msp.id,
        sensor_id=sensor_b.id,
        file_path=FIXTURE_PATH,
    )

    assert result_a.inserted == 3
    assert result_b.inserted == 3
    total = db_session.scalar(select(func.count()).select_from(NetworkEvent))
    assert total == 6


def test_unknown_sensor_and_wrong_msp_rejected(db_session):
    msp, _site, sensor = _build_site(db_session, slug_prefix="import-c")
    other_msp = th.create_msp(db_session, name="Other", slug="msp-import-c-other")

    with pytest.raises(ImportValidationError):
        resolve_sensor_for_import(
            db_session,
            msp_id=msp.id,
            sensor_id=uuid.uuid4(),
        )

    with pytest.raises(ImportValidationError):
        resolve_sensor_for_import(
            db_session,
            msp_id=other_msp.id,
            sensor_id=sensor.id,
        )


def test_db_rejects_cross_site_sensor_relationship(db_session):
    msp, site_a, sensor_a = _build_site(db_session, slug_prefix="import-d")
    customer = th.create_customer(
        db_session,
        msp_id=msp.id,
        name="Customer D2",
        slug="cust-d2",
    )
    site_b = th.create_site(
        db_session,
        msp_id=msp.id,
        customer_id=customer.id,
        name="Site B",
        slug="site-d-b",
    )

    event = NetworkEvent(
        msp_id=msp.id,
        site_id=site_b.id,
        sensor_id=sensor_a.id,
        source_type=NetworkEventSourceType.ZEEK_CONN,
        source_event_id="BADUID001",
        event_at=datetime.now(tz=UTC),
        src_ip="192.0.2.1",
        dst_ip="198.51.100.1",
        src_port=1,
        dst_port=2,
        transport_protocol="tcp",
        source_record={"uid": "BADUID001"},
    )
    db_session.add(event)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_import_reports_rejected_lines_without_commit(db_session, tmp_path):
    msp, _site, sensor = _build_site(db_session, slug_prefix="import-e")
    bad_file = tmp_path / "bad.jsonl"
    bad_file.write_text(
        '{"ts": 1.0, "uid": "OK1", "id": {"orig_h": "192.0.2.1", "resp_h": "198.51.100.1"}, "proto": "tcp"}\n'
        "{invalid-json}\n",
        encoding="utf-8",
    )

    result = import_zeek_conn_file(
        db_session,
        msp_id=msp.id,
        sensor_id=sensor.id,
        file_path=bad_file,
    )
    assert result.inserted == 1
    assert result.rejected_count == 1
    assert result.rejected[0].line_number == 2
    db_session.rollback()
    count = db_session.scalar(select(func.count()).select_from(NetworkEvent))
    assert count == 0
