"""Demo attack scenarios. Each builds one event, starting from a nominal 'typical day' session."""
from datetime import datetime

SCENARIOS = {
    "normal": ("Normal login", "Known laptop, office hours, usual city, typical activity."),
    "new_device": ("New device", "Login from an unrecognised Kali Linux machine."),
    "unusual_location": ("Unusual location", "Login from Lagos, NG (never seen in baseline)."),
    "midnight": ("Midnight login", "Session starting at ~03:00."),
    "download": ("Abnormal download activity", "2.4 GB bulk download with 210 actions."),
    "multiple": ("Account takeover simulation (multiple suspicious actions)", "New device + foreign location + 3 AM + mass download."),
}
# Presentation storyline: gradual account takeover
SAMPLE_ATTACK = [("1. Attacker idle — victim's normal login", "normal"),
                 ("2. Stolen credentials used from a new device", "new_device"),
                 ("3. Same session appears from a foreign location", "unusual_location"),
                 ("4. Off-hours activity at 3 AM", "midnight"),
                 ("5. Mass data exfiltration", "multiple")]

def scenario_event(key):
    e = {"ts": datetime.now(), "hour": 10.3, "device": "Dell-Latitude-Win11", "location": "Hyderabad, IN (Home)",
         "session_min": 44.0, "actions": 58, "downloads_mb": 28.0}
    if key in ("new_device", "multiple"): e["device"] = "Unknown-Kali-Linux"
    if key in ("unusual_location", "multiple"): e["location"] = "Lagos, NG"
    if key in ("midnight", "multiple"): e["hour"] = 3.2
    if key in ("download", "multiple"): e.update(downloads_mb=2400.0, actions=210, session_min=130.0 if key == "multiple" else 44.0)
    return e
