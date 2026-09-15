#!/usr/bin/env python3
"""Verify Phase 4 tables and tenant ownership constraints exist in PostgreSQL."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import inspect, text

from backend.app.database.session import check_database_connection, get_engine

EXPECTED_TABLES = ("msps", "users", "customers", "sites", "sensors", "devices")

EXPECTED_FKS = (
    "fk_sites_customer_msp",
    "fk_sensors_site_msp",
    "fk_devices_site_msp",
)


def main() -> int:
    if not check_database_connection():
        print("ERROR: PostgreSQL is not reachable. Start with: docker compose up -d db")
        return 1

    engine = get_engine()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    missing_tables = [name for name in EXPECTED_TABLES if name not in tables]
    if missing_tables:
        print(f"ERROR: Missing tables: {', '.join(missing_tables)}")
        print("Run: cd backend && alembic -c alembic.ini upgrade head")
        return 1

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT conname
                FROM pg_constraint
                WHERE conname = ANY(:names)
                """
            ),
            {"names": list(EXPECTED_FKS)},
        ).all()
    found = {row[0] for row in rows}
    missing_fks = [name for name in EXPECTED_FKS if name not in found]
    if missing_fks:
        print(f"ERROR: Missing tenant ownership constraints: {', '.join(missing_fks)}")
        return 1

    print("OK: Phase 4 domain tables and tenant ownership constraints are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
