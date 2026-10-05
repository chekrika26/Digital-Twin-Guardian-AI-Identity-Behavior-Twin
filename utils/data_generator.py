"""SIMULATED behavioral data for the prototype (no real user data is used)."""
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

DEVICES = ["Dell-Latitude-Win11", "iPhone-13"]
DEVICE_P = [0.82, 0.18]
LOCS = ["Hyderabad, IN (Home)", "Hyderabad, IN (Office)", "Bengaluru, IN"]
LOC_P = [0.58, 0.39, 0.03]

def normal_events(n=500, seed=None, ts=None):
    """Generate n 'normal' sessions: office-hours logins, known devices/places, modest downloads."""
    rng = np.random.default_rng(seed)
    hour = np.clip(rng.normal(10.5, 1.8, n), 6.5, 20)
    df = pd.DataFrame({
        "hour": hour.round(2),
        "device": rng.choice(DEVICES, n, p=DEVICE_P),
        "location": rng.choice(LOCS, n, p=LOC_P),
        "session_min": np.clip(rng.normal(45, 12, n), 5, None).round(1),
        "actions": np.clip(rng.normal(60, 15, n), 5, None).round().astype(int),
        "downloads_mb": np.clip(rng.normal(30, 15, n), 0, None).round(1),
    })
    if ts is None:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days = rng.integers(1, 30, n)
        df["ts"] = [today - timedelta(days=int(d)) + timedelta(hours=float(h)) for d, h in zip(days, hour)]
    else:
        df["ts"] = ts
    return df.sort_values("ts").reset_index(drop=True)
