"""Turns a risk result into a human-readable SOC alert."""
ACTIONS = {"SUSPICIOUS": "Monitor the session and review the activity log.",
           "HIGH RISK": "Request step-up verification (MFA) before continuing.",
           "CRITICAL": "Challenge with MFA, suspend the session and notify the security team."}

def build_alert(risk):
    top = [f for f in risk["factors"] if f["points"] >= 0.25 * f["max"]]
    top = sorted(top, key=lambda f: -f["points"]) or sorted(risk["factors"], key=lambda f: -f["points"])[:1]
    title = (f"{risk['level']} — Behavioral Identity Mismatch" if risk["level"] in ("CRITICAL", "HIGH RISK")
             else f"{risk['level']} — Behavioral Deviation Detected")
    lines = [f["reason"] for f in top] + [f"Recommended action: {ACTIONS.get(risk['level'], 'None')}", f"Risk Score: {int(round(risk['score']))}/100"]
    return {"title": title, "message": "\n".join(lines)}
