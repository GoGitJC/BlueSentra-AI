"""Import Zeek conn.log JSON Lines into normalized network events."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, TextIO

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.app.models.enums import NetworkEventSourceType
from backend.app.models.network_event import NetworkEvent
from backend.app.models.sensor import Sensor
from backend.app.parsers.zeek_conn import ParsedZeekConnRecord, ZeekConnParseError, parse_zeek_conn_line

DEFAULT_BATCH_SIZE = 500


class ImportValidationError(ValueError):
    pass


@dataclass
class RejectedRecord:
    line_number: int
    reason: str


@dataclass
class ZeekConnImportResult:
    inserted: int = 0
    duplicates: int = 0
    rejected: list[RejectedRecord] = field(default_factory=list)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)


def resolve_sensor_for_import(
    db: Session,
    *,
    msp_id: uuid.UUID,
    sensor_id: uuid.UUID,
) -> Sensor:
    sensor = db.scalar(
        select(Sensor).where(
            Sensor.id == sensor_id,
            Sensor.msp_id == msp_id,
        )
    )
    if sensor is None:
        raise ImportValidationError("Sensor not found for the supplied MSP")
    return sensor


def _row_from_parsed(
    *,
    parsed: ParsedZeekConnRecord,
    msp_id: uuid.UUID,
    site_id: uuid.UUID,
    sensor_id: uuid.UUID,
) -> dict:
    return {
        "msp_id": msp_id,
        "site_id": site_id,
        "sensor_id": sensor_id,
        "device_id": None,
        "source_type": NetworkEventSourceType.ZEEK_CONN,
        "source_event_id": parsed.source_event_id,
        "event_at": parsed.event_at,
        "src_ip": parsed.src_ip,
        "dst_ip": parsed.dst_ip,
        "src_port": parsed.src_port,
        "dst_port": parsed.dst_port,
        "transport_protocol": parsed.transport_protocol,
        "service": parsed.service,
        "duration": parsed.duration,
        "orig_bytes": parsed.orig_bytes,
        "resp_bytes": parsed.resp_bytes,
        "orig_pkts": parsed.orig_pkts,
        "resp_pkts": parsed.resp_pkts,
        "source_record": parsed.source_record,
    }


def _insert_batch(db: Session, rows: list[dict]) -> tuple[int, int]:
    if not rows:
        return 0, 0

    stmt = insert(NetworkEvent).values(rows)
    stmt = stmt.on_conflict_do_nothing(
        constraint="uq_network_events_sensor_source",
    ).returning(NetworkEvent.id)

    inserted_ids = list(db.scalars(stmt))
    db.flush()
    inserted = len(inserted_ids)
    duplicates = len(rows) - inserted
    return inserted, duplicates


def import_zeek_conn_file(
    db: Session,
    *,
    msp_id: uuid.UUID,
    sensor_id: uuid.UUID,
    file_path: Path | str,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> ZeekConnImportResult:
    """
    Stream-parse a Zeek conn.log JSONL file and insert normalized events.

    Transaction behavior: rows are inserted in batches with flush per batch.
    The caller must commit() on success or rollback() on failure. Parse
    rejections are collected and never inserted; valid rows in the same run
    are still inserted unless the caller rolls back the whole session.
    """
    sensor = resolve_sensor_for_import(db, msp_id=msp_id, sensor_id=sensor_id)
    site_id = sensor.site_id

    result = ZeekConnImportResult()
    batch: list[dict] = []

    path = Path(file_path)
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                parsed = parse_zeek_conn_line(line, line_number=line_number)
            except ZeekConnParseError as exc:
                result.rejected.append(
                    RejectedRecord(line_number=exc.line_number, reason=exc.message)
                )
                continue

            batch.append(
                _row_from_parsed(
                    parsed=parsed,
                    msp_id=msp_id,
                    site_id=site_id,
                    sensor_id=sensor_id,
                )
            )

            if len(batch) >= batch_size:
                ins, dup = _insert_batch(db, batch)
                result.inserted += ins
                result.duplicates += dup
                batch.clear()

        if batch:
            ins, dup = _insert_batch(db, batch)
            result.inserted += ins
            result.duplicates += dup

    return result
