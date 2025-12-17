# ---- BlueSentra bootstrap: makes `src.*` imports work in Streamlit ----
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # .../bluesentra-mvp
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# -----------------------------
# Paths (single source of truth)
# -----------------------------
DATA_DIR = REPO_ROOT / "src" / "data"
DATA_DIR = REPO_ROOT / "data"

import os
import sys
import json
import hashlib
import subprocess
import streamlit as st

# -----------------------------
# Path setup (robust)
# -----------------------------

DATA_DIR = REPO_ROOT / "src" / "data"

from src.dashboard.explain import explain_with_openai
from src.dashboard.demo_mode import inject_compromised_camera



# -----------------------------
# Helpers
# -----------------------------
def alert_key(alert_dict: dict) -> str:
    raw = json.dumps(alert_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]

# -----------------------------
# Streamlit config
# -----------------------------
st.set_page_config(
    page_title="BlueSentra AI — MVP",
    layout="wide"
)

st.title("BlueSentra AI — MVP SOC Dashboard")
st.caption("AI-powered anomaly detection & incident triage")

# -----------------------------
# Load data
# -----------------------------

import pandas as pd
import streamlit as st

logs_path = DATA_DIR / "iot_network_logs.csv"
alerts_path = DATA_DIR / "alerts.csv"

logs = pd.read_csv(logs_path)


logs = pd.read_csv(logs_path)
logs["timestamp"] = pd.to_datetime(logs["timestamp"])

alerts = None
if alerts_path.exists():
    alerts = pd.read_csv(alerts_path)
    alerts["timestamp"] = pd.to_datetime(alerts["timestamp"])

# -----------------------------
# Metrics row
# -----------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Log rows", len(logs))
col2.metric("Devices", logs["device_id"].nunique())
col3.metric("Alerts", 0 if alerts is None else len(alerts))

# -----------------------------
# Demo controls
# -----------------------------
st.subheader("Demo Controls")
c1, c2 = st.columns([1, 3])

with c1:
    if st.button("🚨 Inject compromised camera incident"):
        affected = inject_compromised_camera(logs_path)
        st.success(f"Injected incident into {affected} log rows")

        subprocess.run(
    ["python3", str(REPO_ROOT / "src" / "detect_anomalies.py")],
    check=False
            )

        st.rerun()

with c2:
    st.caption(
        "Simulates a compromised smart camera by spiking outbound traffic "
        "and connections in the last 30 minutes."
    )

st.divider()

# -----------------------------
# Alerts view
# -----------------------------
if alerts is not None and len(alerts) > 0:

    left, right = st.columns([1, 2])

    # =========================
    # LEFT COLUMN — Alert Queue
    # =========================
    with left:
        st.subheader("Alert Queue")

        severity_filter = st.multiselect(
            "Severity",
            options=["HIGH", "MEDIUM", "LOW"],
            default=["HIGH", "MEDIUM", "LOW"]
        )

        filt = alerts[alerts["severity"].isin(severity_filter)].copy()

        device_filter = st.selectbox(
            "Filter by device",
            options=["All"] + sorted(filt["device_id"].unique().tolist())
        )

        if device_filter != "All":
            filt = filt[filt["device_id"] == device_filter]

        filt = filt.sort_values(
            ["severity", "timestamp"],
            ascending=[True, False]
        )

        st.dataframe(
            filt[[
                "timestamp",
                "device_id",
                "device_type",
                "severity",
                "anomaly_score"
            ]].head(50),
            use_container_width=True
        )

    # =========================
    # RIGHT COLUMN — Investigation
    # =========================
    with right:
        st.subheader("Investigate an Alert")

        idx = st.number_input(
            "Row index (from filtered table)",
            min_value=0,
            max_value=max(0, len(filt) - 1),
            value=0
        )

        row = filt.iloc[int(idx)]

        st.write(f"**Device:** {row['device_id']} ({row['device_type']})")
        st.write(f"**Time:** {row['timestamp']}")
        st.write(f"**Severity:** {row['severity']}")
        st.write(f"**Score:** {row['anomaly_score']:.6f}")

        st.markdown("### Telemetry")
        st.json({
            "connection_count": int(row["connection_count"]),
            "bytes_sent": int(row["bytes_sent"]),
            "bytes_received": int(row["bytes_received"]),
            "src_ip": row["src_ip"],
            "dst_ip": row["dst_ip"],
        })

        st.markdown("### AI Triage Explanation")

        alert_dict = {
            "timestamp": str(row["timestamp"]),
            "device_id": row["device_id"],
            "device_type": row["device_type"],
            "src_ip": row["src_ip"],
            "dst_ip": row["dst_ip"],
            "connection_count": int(row["connection_count"]),
            "bytes_sent": int(row["bytes_sent"]),
            "bytes_received": int(row["bytes_received"]),
            "severity": row["severity"],
            "anomaly_score": float(row["anomaly_score"]),
        }

        key = alert_key(alert_dict)

        if "explanations" not in st.session_state:
            st.session_state["explanations"] = {}

        colA, colB = st.columns([1, 1])

        with colA:
            if st.button("Generate explanation", key=f"gen_{key}"):
                st.session_state["explanations"][key] = explain_with_openai(alert_dict)

        with colB:
            if st.button("Clear cached explanation", key=f"clr_{key}"):
                st.session_state["explanations"].pop(key, None)

        explanation = st.session_state["explanations"].get(key)

        if explanation:
            st.write(f"**Risk:** {explanation.get('risk_level', row['severity'])}")
            st.write(explanation.get("summary", ""))

            st.markdown("**Why suspicious**")
            st.write(explanation.get("why_suspicious", []))

            st.markdown("**Likely causes**")
            st.write(explanation.get("likely_causes", []))

            st.markdown("**Recommended actions**")
            st.write(explanation.get("recommended_actions", []))

            with st.expander("Raw JSON"):
                st.json(explanation)
        else:
            st.caption("No explanation cached yet. Click 'Generate explanation'.")

else:
    st.warning("No alerts found. Run anomaly detection first.")
