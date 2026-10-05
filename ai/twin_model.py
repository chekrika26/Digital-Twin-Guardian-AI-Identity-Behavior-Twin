"""Digital Twin = statistical baseline of a user's normal behavior + comparison logic."""
import numpy as np
import pandas as pd

KNOWN_MIN = 0.02  # a device/location seen in >=2% of history counts as "known"
NUMERIC = ["session_min", "actions", "downloads_mb"]
FEATURES = ["hour_dev", "session_min", "actions", "downloads_mb", "device_freq", "loc_freq"]

def circ_signed(h, mu):
    """Signed distance on a 24h clock (23:00 vs 01:00 are 2h apart, not 22h)."""
    return ((np.asarray(h, dtype=float) - mu + 12) % 24) - 12

def build_baseline(df):
    """Learn the twin: circular-mean login hour, mean/std of numeric habits, device & location frequencies."""
    ang = df["hour"].to_numpy() * 2 * np.pi / 24
    mu = (np.arctan2(np.sin(ang).mean(), np.cos(ang).mean()) * 24 / (2 * np.pi)) % 24
    b = {"n": int(len(df)), "hour": {"mean": float(mu), "std": float(max(circ_signed(df["hour"], mu).std(), 0.5))}}
    for c in NUMERIC:
        b[c] = {"mean": float(df[c].mean()), "std": float(max(df[c].std(), 1e-6))}
    b["device"] = df["device"].value_counts(normalize=True).to_dict()
    b["location"] = df["location"].value_counts(normalize=True).to_dict()
    return b

def deviations(e, b):
    """Deviation of an event from the twin, in standard deviations (z-scores). Unknown categories = 4.0."""
    z = {"hour": abs(float(circ_signed(e["hour"], b["hour"]["mean"]))) / b["hour"]["std"]}
    for c in NUMERIC:
        z[c] = abs(e[c] - b[c]["mean"]) / b[c]["std"]
    z["device"] = 0.0 if b["device"].get(e["device"], 0) >= KNOWN_MIN else 4.0
    z["location"] = 0.0 if b["location"].get(e["location"], 0) >= KNOWN_MIN else 4.0
    return z

def features(e, b):
    """Numeric vector fed to the Isolation Forest."""
    return [abs(float(circ_signed(e["hour"], b["hour"]["mean"]))), e["session_min"], e["actions"],
            e["downloads_mb"], b["device"].get(e["device"], 0.0), b["location"].get(e["location"], 0.0)]

def match_percent(e, b):
    z = deviations(e, b)
    return float(np.mean([np.clip(1 - v / 5, 0, 1) for v in z.values()]) * 100)

def compare(e, b):
    """Twin vs Reality table."""
    z = deviations(e, b)
    top = lambda d: max(d, key=d.get)
    rows = [("Login time", f"{b['hour']['mean']:.1f}h ± {b['hour']['std']:.1f}", f"{e['hour']:.1f}h", z["hour"]),
            ("Session duration", f"{b['session_min']['mean']:.0f} ± {b['session_min']['std']:.0f} min", f"{e['session_min']:.0f} min", z["session_min"]),
            ("Activity frequency", f"{b['actions']['mean']:.0f} ± {b['actions']['std']:.0f} actions", f"{e['actions']:.0f} actions", z["actions"]),
            ("Download volume", f"{b['downloads_mb']['mean']:.0f} ± {b['downloads_mb']['std']:.0f} MB", f"{e['downloads_mb']:.0f} MB", z["downloads_mb"]),
            ("Device", top(b["device"]), e["device"], z["device"]),
            ("Location", top(b["location"]), e["location"], z["location"])]
    df = pd.DataFrame(rows, columns=["Feature", "Expected (Twin)", "Current", "Deviation"])
    df["Status"] = np.where(df["Deviation"] >= 2, "⚠ Deviation", "✓ Match")
    df["Deviation"] = df["Deviation"].round(2)
    return df
