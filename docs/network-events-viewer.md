# Local Network Events viewer (Streamlit)

The Network Events view is a **localhost-only** read-only dashboard over normalized Zeek `conn.log` rows in PostgreSQL. It is not authenticated and must not be exposed as a multi-user SaaS surface without login, authorization, and deployment hardening.

## Access control

- **MSP scope** is fixed server-side via `BLUESENTRA_VIEWER_MSP_ID` in `.env` (see `.env.example`).
- The browser cannot choose or override tenant ownership.
- All detail and freshness queries constrain `msp_id` in SQL and validate customer/site/sensor relationships before returning data.

## Connection details

Analysts filter and paginate the connection table, then select a row by **immutable event UUID** (never row index). Details include connection endpoints, traffic counters, context (customer, site, sensor, UTC event and ingestion times, source type), and collapsed read-only original Zeek JSON.

- **Originator / responder** follow Zeek conn.log direction. They are not internal/external or benign/malicious labels.
- **Linked device** appears only when a valid `device_id` FK exists and device metadata is present.
- Missing optional fields display as unknown (—).

Unavailable, out-of-scope, or wrong-MSP event IDs show the same user-facing unavailable state.

## Data freshness

The **Data freshness** panel summarizes **stored records** for the selected customer/site/sensor scope. It does **not** use the table’s UTC time filter.

| Label | Meaning |
|--------|---------|
| **Latest observed activity** | `MAX(event_at)` in scope — when the network activity occurred. |
| **Latest stored-event ingestion** | `MAX(ingested_at)` in scope — when the newest stored row was written. |

Importing an old log today can make ingestion recent while activity timestamps remain historical. **Duplicate-only re-imports** do not insert rows and therefore do not advance stored-event ingestion maxima. There is no import-run audit table yet; these metrics are not “last import attempt” or “last successful import operation.”

If the table time window excludes the latest observed activity in scope, the UI explains that freshness still reflects all stored events in that scope.

## Launch

```bash
docker compose up -d db
cd backend && alembic -c alembic.ini upgrade head
# Set BLUESENTRA_VIEWER_MSP_ID to your MSP UUID in .env

BLUESENTRA_VIEWER_MSP_ID=<msp-uuid> \
  streamlit run src/dashboard/app.py --server.address=127.0.0.1 --server.port=8501
```

Refresh reloads the table, summaries, and freshness together. The “last refreshed” caption updates only after those queries succeed.
