import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

DEVICES = [
    {"device_id": "cam_livingroom", "device_type": "camera"},
    {"device_id": "thermostat_hall", "device_type": "thermostat"},
    {"device_id": "plug_bedroom", "device_type": "smart_plug"},
    {"device_id": "lock_frontdoor", "device_type": "smart_lock"},
    {"device_id": "speaker_kitchen", "device_type": "smart_speaker"},
]

def gen_ip():
    return f"192.168.1.{random.randint(2, 254)}"

def main(out_path="data/iot_network_logs.csv", hours=48, interval_minutes=5):
    os.makedirs("data", exist_ok=True)

    start = datetime.now() - timedelta(hours=hours)
    timestamps = [start + timedelta(minutes=interval_minutes*i) for i in range(int((hours*60)/interval_minutes))]

    rows = []
    for ts in timestamps:
        for d in DEVICES:
            base_conn = {
                "camera": 25,
                "thermostat": 6,
                "smart_plug": 3,
                "smart_lock": 2,
                "smart_speaker": 10,
            }[d["device_type"]]

            # normal behavior + noise
            conn_count = max(0, int(np.random.normal(base_conn, base_conn * 0.2)))
            bytes_sent = max(0, int(np.random.normal(12000 * base_conn, 4000 * base_conn)))
            bytes_recv = max(0, int(np.random.normal(18000 * base_conn, 5000 * base_conn)))

            # inject anomalies sometimes (spikes, weird hours)
            if np.random.rand() < 0.01:
                conn_count *= random.randint(6, 15)
                bytes_sent *= random.randint(5, 12)
                bytes_recv *= random.randint(5, 12)

            rows.append({
                "timestamp": ts.isoformat(timespec="seconds"),
                "device_id": d["device_id"],
                "device_type": d["device_type"],
                "src_ip": gen_ip(),
                "dst_ip": f"{random.randint(20, 200)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
                "connection_count": conn_count,
                "bytes_sent": bytes_sent,
                "bytes_received": bytes_recv
            })

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    print(f"✅ Wrote {len(df)} rows to {out_path}")

if __name__ == "__main__":
    main()
