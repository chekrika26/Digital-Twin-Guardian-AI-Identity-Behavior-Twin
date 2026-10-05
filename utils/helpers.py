"""Glue code: bootstrap (DB + twin + model), event recording, query helpers."""
import json
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import text
from database.database import SessionLocal, engine, init_db
from database.models import Activity, Alert, AnomalyEvent, Profile, RiskScore, User
from ai.twin_model import build_baseline
from ai.anomaly_detector import TwinDetector
from security.risk_engine import compute_risk
from security.alert_engine import build_alert
from simulator.attack_simulator import scenario_event
from utils.data_generator import normal_events

COLORS = {"SAFE": "#22c55e", "SUSPICIOUS": "#facc15", "HIGH RISK": "#fb923c", "CRITICAL": "#ef4444"}

def record_event(e, uid, b, det, label="live", session=None):
    """Score one event with the twin + ML model and persist activity, anomaly, risk and alert rows."""
    an = det.score(e)
    risk = compute_risk(e, b, an)
    s = session or SessionLocal()
    a = Activity(user_id=uid, ts=e["ts"], hour=float(e["hour"]), device=str(e["device"]), location=str(e["location"]),
                 session_min=float(e["session_min"]), actions=int(e["actions"]), downloads_mb=float(e["downloads_mb"]), label=label)
    s.add(a); s.flush()
    s.add(AnomalyEvent(activity_id=a.id, anomaly_score=an, ts=e["ts"]))
    s.add(RiskScore(activity_id=a.id, score=risk["score"], level=risk["level"], ts=e["ts"]))
    alert = None
    if risk["score"] > 30:
        alert = build_alert(risk)
        s.add(Alert(activity_id=a.id, severity=risk["level"], title=alert["title"], message=alert["message"], score=risk["score"], ts=e["ts"]))
    if session is None:
        s.commit(); s.close()
    return {**risk, "anomaly": an, "alert": alert}

def _normal_rows():
    return pd.read_sql(text("SELECT * FROM activities WHERE label='normal'"), engine)

def bootstrap():
    """Create DB, seed synthetic history on first run, train the twin and the Isolation Forest."""
    init_db()
    with SessionLocal() as s:
        u = s.query(User).first()
        if not u:
            u = User(username="alex.morgan", role="Finance Analyst"); s.add(u); s.commit()
        uid, n = u.id, s.query(Activity).count()
    if n == 0:
        seed = normal_events(500, seed=42)
        b = build_baseline(seed); det = TwinDetector(b, seed)
        with SessionLocal() as s:
            for r in seed.to_dict("records"):
                r["ts"] = pd.Timestamp(r["ts"]).to_pydatetime()
                record_event(r, uid, b, det, "normal", s)
            keys = ["new_device", "unusual_location", "midnight", "download", "multiple", "new_device", "midnight", "download"]
            for i, k in enumerate(keys):  # a few past incidents so the dashboard has history
                r = scenario_event(k); r["ts"] = datetime.now() - timedelta(days=9 - i, hours=i * 2)
                record_event(r, uid, b, det, "history", s)
            s.commit()
    df = _normal_rows()
    b = build_baseline(df); det = TwinDetector(b, df)
    with SessionLocal() as s:
        s.add(Profile(user_id=uid, data=json.dumps(b))); s.commit()
    return uid, b, det

def load_df():
    q = """SELECT a.*, r.score, r.level, n.anomaly_score FROM activities a
           JOIN risk_scores r ON r.activity_id=a.id JOIN anomaly_events n ON n.activity_id=a.id ORDER BY a.ts"""
    df = pd.read_sql(text(q), engine)
    df["ts"] = pd.to_datetime(df["ts"])
    return df

def load_alerts():
    df = pd.read_sql(text("SELECT * FROM alerts ORDER BY ts DESC"), engine)
    df["ts"] = pd.to_datetime(df["ts"])
    return df
