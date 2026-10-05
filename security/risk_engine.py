"""Risk engine: rule-based factors (explainable) + ML anomaly score -> 0-100 risk."""
from ai.twin_model import deviations

# Max points per factor (sum = 100)
WEIGHTS = {"device": 28, "location": 24, "hour": 20, "session_min": 8, "actions": 8, "downloads_mb": 18, "anomaly": 20}  # sum capped at 100
REASONS = {"device": "Unknown device detected.", "location": "Login location differs from baseline.",
           "hour": "Login time is outside the user's normal hours.", "session_min": "Abnormal session duration.",
           "actions": "Unusual activity frequency.", "downloads_mb": "Suspicious download volume.",
           "anomaly": "Isolation Forest flags the overall behavior as an outlier."}

def level_for(score):
    return "SAFE" if score <= 30 else "SUSPICIOUS" if score <= 60 else "HIGH RISK" if score <= 80 else "CRITICAL"

def _ramp(z, w, lo=1.5, hi=4.0):
    """0 points below 1.5 sigma (normal variation), full weight at 4 sigma."""
    return w * min(1.0, max(0.0, (z - lo) / (hi - lo)))

def compute_risk(e, b, anomaly):
    z = deviations(e, b)
    pts = {k: _ramp(z[k], w) for k, w in WEIGHTS.items() if k != "anomaly"}
    pts["anomaly"] = WEIGHTS["anomaly"] * min(1.0, anomaly / 50)  # ML signal saturates at anomaly 50
    score = round(min(100.0, sum(pts.values())), 1)
    factors = [{"factor": k, "points": round(p, 1), "max": WEIGHTS[k], "reason": REASONS[k]} for k, p in pts.items()]
    return {"score": score, "level": level_for(score), "factors": factors}
