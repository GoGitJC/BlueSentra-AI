# BlueSentra Architecture

## Current state (repository)

### Prototype (`src/`)

- **Telemetry:** Simulated IoT network logs (`src/dashboard/generate_logs.py`) → CSV.
- **Detection:** Global Isolation Forest on `connection_count`, `bytes_sent`, `bytes_received` (`src/core/detect_anomalies.py`) → `src/data/alerts.csv`.
- **Dashboard:** Streamlit (`src/dashboard/app.py`) with optional OpenAI triage (`src/dashboard/explain.py`).
- **Demo:** Injected “compromised camera” scenario (`src/dashboard/demo_mode.py`).

### Backend foundation (`backend/`)

- **API:** FastAPI with versioned prefix `/api/v1`.
- **Database:** PostgreSQL via SQLAlchemy 2.x; Alembic migration `20260314_0001` creates MSP, User, Customer, Site, Sensor, and Device with explicit `msp_id` scoping and composite foreign keys to prevent cross-tenant hierarchy mistakes.
- **Services:** `backend/app/services/tenant_hierarchy.py` creates tenant-owned records (flush-only; caller commits).
- **Tenant scoping:** `backend/app/core/tenant.py` requires an explicit `msp_id` for scoped queries and lookups. Composite foreign keys enforce that sites, sensors, and devices cannot reference resources owned by another MSP at the **database relationship** layer.
- **Not the same as auth isolation:** There is no authentication or authenticated authorization yet. Any future API must bind requests to an MSP identity and apply these scoping helpers (or equivalent) on every query — relationship integrity alone does not protect a deployed API without auth.
- **Deploy:** `docker-compose.yml` (Postgres + API).
- **Network events (Phase 5A):** Table `network_events` stores normalized connection telemetry with JSONB `source_record`. Migration `20260314_0002` adds composite tenant/site/sensor (and optional device) constraints.
- **Zeek conn import:** `backend/app/parsers/zeek_conn.py` maps Zeek Conn::Info fields; `scripts/import_zeek_conn.py` streams JSON Lines in batches with `INSERT … ON CONFLICT DO NOTHING` on `uq_network_events_sensor_source` (`sensor_id`, `source_type`, `source_event_id`). Assumes Zeek `uid` is unique per sensor export. Originator/responder fields are stored as observed — not interpreted as internal vs external.
- **References:** [Zeek conn.log / Conn::Info](https://docs.zeek.org/en/current/scripts/base/protocols/conn/main.zeek.html)

## Target architecture (planned)

```text
Customer Network
        ↓
Zeek + Suricata
        ↓
BlueSentra Sensor
        ↓
FastAPI Ingestion API
        ↓
PostgreSQL
        ↓
Baseline + Detection Engine (BS-001 … BS-005)
        ↓
Alerts
        ↓
MSP Dashboard
```

Tenant hierarchy: MSP → Customer → Site → Sensor/Device → **Events (Zeek conn via CLI)** → Detections → Alerts (detections/alerts **planned**).

Primary detection should remain deterministic (telemetry, signatures, statistical baselines). AI may assist explanations later; it is not the core decision engine for MVP.
