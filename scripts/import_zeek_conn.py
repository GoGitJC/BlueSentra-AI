#!/usr/bin/env python3
"""Import a local Zeek conn.log JSON Lines file into PostgreSQL."""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.database.session import get_session_factory
from backend.app.services.zeek_conn_import import ImportValidationError, import_zeek_conn_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Zeek conn.log JSONL into BlueSentra")
    parser.add_argument("--msp-id", required=True, type=uuid.UUID)
    parser.add_argument("--sensor-id", required=True, type=uuid.UUID)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"ERROR: file not found: {args.file}", file=sys.stderr)
        return 2

    db = get_session_factory()()
    try:
        try:
            result = import_zeek_conn_file(
                db,
                msp_id=args.msp_id,
                sensor_id=args.sensor_id,
                file_path=args.file,
                batch_size=args.batch_size,
            )
        except ImportValidationError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

        if result.rejected:
            db.rollback()
            print(
                f"inserted=0 duplicates=0 rejected={result.rejected_count}",
                file=sys.stderr,
            )
            for item in result.rejected:
                print(f"  line {item.line_number}: {item.reason}", file=sys.stderr)
            return 1

        db.commit()
        print(
            f"inserted={result.inserted} duplicates={result.duplicates} "
            f"rejected={result.rejected_count}"
        )
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
