# BlueSentra Architecture

## Current state (repository)

### Prototype (`src/`)

- **Telemetry:** Simulated IoT network logs (`src/dashboard/generate_logs.py`) → CSV.
- **Detection:** Global Isolation Forest on `connection_count`, `bytes_sent`, `bytes_received` (`src/core/detect_anomalies.py`) → `src/data/alerts.csv`.
- **Dashboard:** Streamlit (`src/dashboard/app.py`) with optional OpenAI triage (`src/dashboard/explain.py`).
- **Demo:** Injected “compromised camera” scenario (`src/dashboard/demo_mode.py`).

### Backend foundation (`backend/`)

- **API:** FastAPI with versioned prefix `/api/v1`.
- **Database:** PostgreSQL via SQLAlchemy 2.x; Alembic migrations scaffold (no domain tables yet).
- **Deploy:** `docker-compose.yml` (Postgres + API).

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

Tenant hierarchy (planned): MSP → Customer → Site → Sensor/Device → Events → Detections → Alerts.

Primary detection should remain deterministic (telemetry, signatures, statistical baselines). AI may assist explanations later; it is not the core decision engine for MVP.
