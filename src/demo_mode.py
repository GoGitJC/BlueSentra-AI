import pandas as pd
from datetime import timedelta

def inject_compromised_camera(logs_path: str, device_id="cam_livingroom"):
    df = pd.read_csv(logs_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    latest = df["timestamp"].max()
    start = latest - timedelta(minutes=30)

    mask = (df["device_id"] == device_id) & (df["timestamp"] >= start)

    df.loc[mask, "connection_count"] = (
        df.loc[mask, "connection_count"] * 12
    ).clip(upper=5000).astype(int)

    df.loc[mask, "bytes_sent"] = (
        df.loc[mask, "bytes_sent"] * 10
    ).clip(upper=20_000_000).astype(int)

    df.loc[mask, "bytes_received"] = (
        df.loc[mask, "bytes_received"] * 10
    ).clip(upper=20_000_000).astype(int)

    df.loc[mask, "dst_ip"] = "185.199.110.153"

    df.to_csv(logs_path, index=False)
    return int(mask.sum())
