from datetime import UTC, datetime

import pytest

from backend.app.parsers.zeek_conn import ZeekConnParseError, parse_zeek_conn_line


def test_maps_nested_id_fields_and_optional_values():
    line = (
        '{"ts": 1700000000.0, "uid": "U1", "id": {"orig_h": "192.0.2.10", "orig_p": 1234, '
        '"resp_h": "198.51.100.20", "resp_p": 443}, "proto": "tcp", "service": "ssl", '
        '"duration": 1.5, "orig_bytes": 100, "resp_bytes": 200, "orig_pkts": 3, "resp_pkts": 4}'
    )
    parsed = parse_zeek_conn_line(line, line_number=1)
    assert parsed.source_event_id == "U1"
    assert parsed.event_at == datetime.fromtimestamp(1700000000.0, tz=UTC)
    assert parsed.src_ip == "192.0.2.10"
    assert parsed.dst_ip == "198.51.100.20"
    assert parsed.src_port == 1234
    assert parsed.dst_port == 443
    assert parsed.transport_protocol == "tcp"
    assert parsed.service == "ssl"
    assert parsed.duration == 1.5
    assert parsed.orig_bytes == 100
    assert parsed.resp_bytes == 200
    assert parsed.orig_pkts == 3
    assert parsed.resp_pkts == 4


def test_missing_optional_fields_are_null():
    line = (
        '{"ts": 1700000001.0, "uid": "U2", "id": {"orig_h": "192.0.2.11", "orig_p": 53, '
        '"resp_h": "198.51.100.21", "resp_p": 53}, "proto": "udp"}'
    )
    parsed = parse_zeek_conn_line(line, line_number=2)
    assert parsed.service is None
    assert parsed.duration is None
    assert parsed.orig_bytes is None
    assert parsed.resp_bytes is None
    assert parsed.orig_pkts is None
    assert parsed.resp_pkts is None


def test_zeek_dash_and_null_optional_values():
    line = (
        '{"ts": 1700000002.0, "uid": "U3", "id": {"orig_h": "192.0.2.12", "orig_p": 80, '
        '"resp_h": "198.51.100.22", "resp_p": 8080}, "proto": "tcp", "duration": "-", '
        '"orig_bytes": null}'
    )
    parsed = parse_zeek_conn_line(line, line_number=3)
    assert parsed.duration is None
    assert parsed.orig_bytes is None


def test_invalid_json_raises_with_line_number():
    with pytest.raises(ZeekConnParseError) as exc:
        parse_zeek_conn_line("{not-json", line_number=7)
    assert exc.value.line_number == 7
    assert "invalid JSON" in exc.value.message


def test_missing_required_uid():
    line = '{"ts": 1.0, "id": {"orig_h": "192.0.2.1", "resp_h": "198.51.100.1"}, "proto": "tcp"}'
    with pytest.raises(ZeekConnParseError) as exc:
        parse_zeek_conn_line(line, line_number=4)
    assert exc.value.line_number == 4
    assert "uid" in exc.value.message
