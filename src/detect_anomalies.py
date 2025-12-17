import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


FEATURES = ["connection_count", "bytes_sent", "bytes_received"]

def main(
    in_path="data/iot_network_logs.csv",
    out_path="data/alerts.csv",
    contamination=0.02
):
    df = pd.read_csv(os.path.join(DATA_DIR, "iot_network_logs.csv"))

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Basic cleanup
    for c in FEATURES:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Train one model across all devices (simple MVP)
    X = df[FEATURES].values

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42
    )
    preds = model.fit_predict(X)  # -1 = anomaly, 1 = normal
    scores = model.decision_function(X)  # lower = more anomalous

    df["is_anomaly"] = (preds == -1)
    df["anomaly_score"] = scores

    alerts = df[df["is_anomaly"]].copy()

    # Add a simple severity bucket
    # (more negative score => more severe)
    q1 = alerts["anomaly_score"].quantile(0.33) if len(alerts) else 0
    q2 = alerts["anomaly_score"].quantile(0.66) if len(alerts) else 0

    def sev(s):
        if s <= q1: return "HIGH"
        if s <= q2: return "MEDIUM"
        return "LOW"

    alerts["severity"] = alerts["anomaly_score"].apply(sev)

    os.makedirs("data", exist_ok=True)
    alerts.sort_values(["severity", "timestamp"]).to_csv(os.path.join(DATA_DIR, "alerts.csv"), index=False)

    print(f"✅ Detected {len(alerts)} anomalies → {out_path}")

if __name__ == "__main__":
    main()
