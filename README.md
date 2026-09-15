# BlueSentra

## Agentless Network Detection & Visibility for MSPs

BlueSentra is a multi-tenant network detection platform designed for Managed Service Providers.

BlueSentra passively analyzes network telemetry to identify suspicious behavioral changes across managed and unmanaged devices without requiring traditional endpoint agents.

**See suspicious behavior across the devices your endpoint agents can't reach.**

> **Status:** Under active development. Not production-ready. Capabilities below distinguish what exists today from what is planned.

---

## What exists today

| Area | Status |
|------|--------|
| Streamlit SOC dashboard (CSV-backed) | **Implemented** (prototype) |
| Simulated IoT traffic + demo incident injection | **Implemented** |
| Isolation Forest anomaly scoring on aggregate features | **Implemented** (experimental, not per-device baselines) |
| Optional OpenAI alert explanations | **Implemented** (optional; rule-based fallback) |
| FastAPI `/api/v1/health` + `/api/v1/ready` | **Implemented** |
| PostgreSQL + SQLAlchemy + Alembic multi-tenant domain | **Implemented** (MSP → User → Customer → Site → Sensor/Device) |
| Database relationship / tenant ownership constraints | **Implemented** (composite FKs + `msp_id` scoping helpers) |
| Authenticated MSP access isolation (login, tokens, authorization) | **Planned** |
| REST CRUD for tenants / events / alerts | **Planned** |
| Zeek / Suricata ingestion, BS-001–BS-005 detections | **Planned** |

---

## Repository layout

```text
src/                 # Original prototype (dashboard, detection, CSV data)
backend/             # FastAPI application, Alembic, tests
docker/              # Container definitions
docs/                # Architecture notes
```

Target flow (in progress):

```text
Network Telemetry → Normalized Events → BlueSentra Backend → PostgreSQL
  → Detection Engine → Alerts → Dashboard
```

---

## Run the API (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
docker compose up -d db

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: http://localhost:8000/api/v1/health  
- Readiness (checks DB): http://localhost:8000/api/v1/ready — HTTP **200** when PostgreSQL is connected, HTTP **503** when unavailable  
- OpenAPI: http://localhost:8000/docs  

Full stack via Docker:

```bash
docker compose up --build
```

Alembic (from repo root, after DB is up):

```bash
cd backend && alembic -c alembic.ini upgrade head
python scripts/seed_demo_tenant.py
```

---

## Run the Streamlit prototype

```bash
source .venv/bin/activate
pip install -r requirements.txt

# Regenerate sample logs (optional)
python src/dashboard/generate_logs.py

# Run detection → writes src/data/alerts.csv
python src/core/detect_anomalies.py

streamlit run src/dashboard/app.py
```

---

## Tests

```bash
docker compose up -d db
cd backend && alembic -c alembic.ini upgrade head
cd ..
python scripts/verify_phase4_schema.py
python scripts/seed_demo_tenant.py   # safe to run repeatedly (idempotent)
pytest
```

PostgreSQL integration tests are **skipped** when the database is not reachable. A skipped result is not a passing integration run.

---

## Documentation

- Architecture overview: `docs/architecture.md`
- Research paper (healthcare-focused prototype): `docs/BlueSentra_AI_Agentless_IoT_Threat_Detection_in_Outpatient_Healthcare.pdf` (historical context)

---

## License

MIT License © 2025 Jonathan Daniel Campbell
