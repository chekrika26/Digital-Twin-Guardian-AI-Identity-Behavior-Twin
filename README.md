# Digital Twin Guardian — AI Identity Behavior Twin
College prototype (Python 3.11 + Streamlit). **All behavioral data is simulated.**

## Run (Windows)
```
py -3.11 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
## How it works
1. **Digital Twin** – statistics of normal behavior (login hour, session length, activity, downloads, known devices/locations).
2. **Isolation Forest** – trained on normal sessions only; outliers get a 0–100 anomaly score.
3. **Risk engine** – rule factors (device, location, time, session, activity, downloads) + up to 20 pts from the ML anomaly score.
4. **Alerts** – any score >30 creates a stored alert.
## Demo
Attack Simulator → "Run sample account-takeover story": risk climbs from SAFE to CRITICAL.
