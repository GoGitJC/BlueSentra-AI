"""CSV-backed prototype SOC dashboard (unchanged behavior)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
import streamlit as st

from src.dashboard.demo_mode import inject_compromised_camera
from src.dashboard.explain import explain_with_openai
from src.dashboard.theme import ICON_GLOBE, ICON_LINK, render_metric_card, render_page_intro


def alert_key(alert_dict: dict) -> str:
    raw = json.dumps(alert_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


def render(*, repo_root: Path, data_dir: Path) -> None:
    render_page_intro(
        title="Prototype Demo Analysis",
        subtitle="Simulated CSV telemetry and experimental anomaly alerts — separate from imported PostgreSQL events.",
        demo_badge="Synthetic demo data",
    )

    logs_path = data_dir / "iot_network_logs.csv"
    alerts_path = data_dir / "alerts.csv"

    logs = pd.read_csv(logs_path)
    logs["timestamp"] = pd.to_datetime(logs["timestamp"])

    alerts = None
    if alerts_path.exists():
        alerts = pd.read_csv(alerts_path)
        alerts["timestamp"] = pd.to_datetime(alerts["timestamp"])

    st.caption(
        "Prototype metrics use simulated CSV rows only. They do not reflect PostgreSQL network events."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card("Simulated log rows", f"{len(logs):,}", ICON_LINK)
    with c2:
        render_metric_card("Simulated devices", f"{logs['device_id'].nunique():,}", ICON_GLOBE)
    with c3:
        render_metric_card(
            "Prototype alerts",
            f"{0 if alerts is None else len(alerts):,}",
            ICON_LINK,
            help_text="Experimental Isolation Forest alerts from CSV — not production detections.",
        )

    with st.container(border=True):
        st.markdown('<p class="bs-section-label">Demo controls</p>', unsafe_allow_html=True)
        demo_col1, demo_col2 = st.columns([1, 3])
        with demo_col1:
            if st.button("Inject compromised camera incident"):
                affected = inject_compromised_camera(str(logs_path))
                st.success(f"Injected incident into {affected} log rows")
                subprocess.run(
                    ["python3", str(repo_root / "src" / "core" / "detect_anomalies.py")],
                    check=False,
                )
                st.rerun()
        with demo_col2:
            st.caption(
                "Simulates a compromised smart camera by spiking outbound traffic "
                "and connections in the last 30 minutes."
            )

    if alerts is not None and len(alerts) > 0:
        left, right = st.columns([1, 2])

        with left:
            st.markdown('<p class="bs-section-title">Prototype alert queue</p>', unsafe_allow_html=True)
            severity_filter = st.multiselect(
                "Severity",
                options=["HIGH", "MEDIUM", "LOW"],
                default=["HIGH", "MEDIUM", "LOW"],
            )
            filt = alerts[alerts["severity"].isin(severity_filter)].copy()
            device_filter = st.selectbox(
                "Filter by device",
                options=["All"] + sorted(filt["device_id"].unique().tolist()),
            )
            if device_filter != "All":
                filt = filt[filt["device_id"] == device_filter]
            filt = filt.sort_values(["severity", "timestamp"], ascending=[True, False])
            st.dataframe(
                filt[
                    ["timestamp", "device_id", "device_type", "severity", "anomaly_score"]
                ].head(50),
                use_container_width=True,
            )

        with right:
            st.markdown('<p class="bs-section-title">Investigate alert</p>', unsafe_allow_html=True)
            idx = st.number_input(
                "Row index (from filtered table)",
                min_value=0,
                max_value=max(0, len(filt) - 1),
                value=0,
            )
            row = filt.iloc[int(idx)]
            st.write(f"**Device:** {row['device_id']} ({row['device_type']})")
            st.write(f"**Time:** {row['timestamp']}")
            st.write(f"**Severity:** {row['severity']}")
            st.write(f"**Score:** {row['anomaly_score']:.6f}")
            st.markdown("### Telemetry")
            st.json(
                {
                    "connection_count": int(row["connection_count"]),
                    "bytes_sent": int(row["bytes_sent"]),
                    "bytes_received": int(row["bytes_received"]),
                    "src_ip": row["src_ip"],
                    "dst_ip": row["dst_ip"],
                }
            )
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
