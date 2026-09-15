"""
Parse Zeek conn.log JSON Lines records.

Field semantics reference: Zeek conn.log / Conn::Info record
https://docs.zeek.org/en/current/scripts/base/protocols/conn/main.zeek.html
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


class ZeekConnParseError(Exception):
    def __init__(self, line_number: int, message: str) -> None:
        self.line_number = line_number
        self.message = message
        super().__init__(f"line {line_number}: {message}")


@dataclass(frozen=True)
class ParsedZeekConnRecord:
    source_event_id: str
    event_at: datetime
    src_ip: str
    dst_ip: str
    src_port: int | None
    dst_port: int | None
    transport_protocol: str
    service: str | None
    duration: float | None
    orig_bytes: int | None
    resp_bytes: int | None
    orig_pkts: int | None
    resp_pkts: int | None
    source_record: dict[str, Any]


def _zeek_null(value: Any) -> bool:
    return value is None or value == "-" or value == ""


def _optional_str(value: Any) -> str | None:
    if _zeek_null(value):
        return None
    return str(value)


def _optional_int(value: Any, *, line_number: int, field: str) -> int | None:
    if _zeek_null(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ZeekConnParseError(line_number, f"{field} must be an integer") from exc


def _optional_float(value: Any, *, line_number: int, field: str) -> float | None:
    if _zeek_null(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ZeekConnParseError(line_number, f"{field} must be a number") from exc


def _require_str(record: dict[str, Any], key: str, *, line_number: int) -> str:
    value = record.get(key)
    if _zeek_null(value):
        raise ZeekConnParseError(line_number, f"missing required field '{key}'")
    return str(value)


def _extract_id_fields(record: dict[str, Any], *, line_number: int) -> tuple[str, int | None, str, int | None]:
    id_block = record.get("id")
    if isinstance(id_block, dict):
        orig_h = id_block.get("orig_h")
        orig_p = id_block.get("orig_p")
        resp_h = id_block.get("resp_h")
        resp_p = id_block.get("resp_p")
    else:
        orig_h = record.get("id.orig_h")
        orig_p = record.get("id.orig_p")
        resp_h = record.get("id.resp_h")
        resp_p = record.get("id.resp_p")

    if _zeek_null(orig_h) or _zeek_null(resp_h):
        raise ZeekConnParseError(line_number, "missing required connection endpoint IPs (id.orig_h / id.resp_h)")

    src_ip = str(orig_h)
    dst_ip = str(resp_h)
    src_port = _optional_int(orig_p, line_number=line_number, field="id.orig_p")
    dst_port = _optional_int(resp_p, line_number=line_number, field="id.resp_p")
    return src_ip, src_port, dst_ip, dst_port


def parse_ts(value: Any, *, line_number: int) -> datetime:
    if _zeek_null(value):
        raise ZeekConnParseError(line_number, "missing required field 'ts'")
    try:
        epoch = float(value)
    except (TypeError, ValueError) as exc:
        raise ZeekConnParseError(line_number, "ts must be a numeric epoch timestamp") from exc
    return datetime.fromtimestamp(epoch, tz=UTC)


def parse_zeek_conn_line(line: str, *, line_number: int) -> ParsedZeekConnRecord:
    stripped = line.strip()
    if not stripped:
        raise ZeekConnParseError(line_number, "empty line")

    try:
        record = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ZeekConnParseError(line_number, f"invalid JSON: {exc.msg}") from exc

    if not isinstance(record, dict):
        raise ZeekConnParseError(line_number, "JSON value must be an object")

    uid = _require_str(record, "uid", line_number=line_number)
    proto = _require_str(record, "proto", line_number=line_number)
    event_at = parse_ts(record.get("ts"), line_number=line_number)
    src_ip, src_port, dst_ip, dst_port = _extract_id_fields(record, line_number=line_number)

    return ParsedZeekConnRecord(
        source_event_id=uid,
        event_at=event_at,
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        transport_protocol=proto.lower(),
        service=_optional_str(record.get("service")),
        duration=_optional_float(record.get("duration"), line_number=line_number, field="duration"),
        orig_bytes=_optional_int(record.get("orig_bytes"), line_number=line_number, field="orig_bytes"),
        resp_bytes=_optional_int(record.get("resp_bytes"), line_number=line_number, field="resp_bytes"),
        orig_pkts=_optional_int(record.get("orig_pkts"), line_number=line_number, field="orig_pkts"),
        resp_pkts=_optional_int(record.get("resp_pkts"), line_number=line_number, field="resp_pkts"),
        source_record=record,
    )
