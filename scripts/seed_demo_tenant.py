#!/usr/bin/env python3
"""Seed a demo MSP hierarchy for local development (idempotent)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select

from backend.app.database.session import get_session_factory
from backend.app.models.enums import SensorStatus, UserRole
from backend.app.models.msp import MSP
from backend.app.services import tenant_hierarchy as th

DEMO_MSP_SLUG = "demo-msp"


def main() -> None:
    db = get_session_factory()()
    try:
        existing = db.scalar(select(MSP).where(MSP.slug == DEMO_MSP_SLUG))
        if existing is not None:
            print(
                f"Demo tenant already present (msp_id={existing.id}, slug={DEMO_MSP_SLUG}); "
                "skipping seed."
            )
            return

        msp = th.create_msp(db, name="Demo MSP", slug=DEMO_MSP_SLUG)
        th.create_user(
            db,
            msp_id=msp.id,
            email="admin@demo-msp.example",
            full_name="Demo Admin",
            role=UserRole.MSP_ADMIN,
        )
        customer = th.create_customer(
            db,
            msp_id=msp.id,
            name="Acme Clinic",
            slug="acme-clinic",
        )
        site = th.create_site(
            db,
            msp_id=msp.id,
            customer_id=customer.id,
            name="Main Office",
            slug="main-office",
            timezone="America/Chicago",
        )
        th.create_sensor(
            db,
            msp_id=msp.id,
            site_id=site.id,
            name="Edge Sensor 1",
            slug="edge-1",
            status=SensorStatus.ACTIVE,
        )
        th.create_device(
            db,
            msp_id=msp.id,
            site_id=site.id,
            hostname="nas-01",
            mac_address="00:11:22:33:44:55",
            ip_address="192.168.10.50",
            device_type="nas",
        )
        db.commit()
        print(f"Seeded demo tenant MSP id={msp.id} slug={msp.slug}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
