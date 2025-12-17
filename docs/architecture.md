# BlueSentra AI Architecture (MVP)

## Components
- Dashboard (Dash): visualizes device behavior, anomalies, and explanations
- Core: feature extraction, baseline modeling, anomaly scoring, explanations
- Data: simulated telemetry used for MVP validation
- Future Edge: Raspberry Pi collectors to ingest real telemetry

## Data Flow
Telemetry → Feature extraction → Baseline compare → Anomaly score → Explanation → Dashboard
