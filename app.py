"""Digital Twin Guardian — AI Identity Behavior Twin (college prototype, SIMULATED data)."""
import random
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from sqlalchemy import text
from ai.twin_model import compare, match_percent
from database.database import DB_PATH, engine, reset_db
from security.risk_engine import WEIGHTS, compute_risk, level_for
from simulator.attack_simulator import SAMPLE_ATTACK, SCENARIOS, scenario_event
from utils.data_generator import normal_events
from utils.helpers import COLORS, bootstrap, load_alerts, load_df, record_event

st.set_page_config(page_title="Digital Twin Guardian", page_icon="🛡️", layout="wide")
BG = "#0f1829"
st.markdown("""<style>
.block-container{padding-top:1.5rem;max-width:1400px}
.card{background:#111a2e;border:1px solid #1f2d4a;border-radius:12px;padding:16px 18px;margin-bottom:10px}
.card .l{color:#8aa0c4;font-size:.72rem;letter-spacing:.12em;text-transform:uppercase}
.card .v{font-size:2rem;font-weight:700;line-height:1.2}.card .s{color:#8aa0c4;font-size:.8rem}
.alert{border-left:5px solid;border-radius:8px;background:#111a2e;padding:12px 16px;margin-bottom:10px;white-space:pre-line}
.bar{height:12px;border-radius:6px;background:#1f2d4a;overflow:hidden}.bar div{height:100%}
h1,h2,h3{letter-spacing:.02em}.tag{color:#00e5ff;font-size:.75rem;letter-spacing:.2em}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def get_state():
    return bootstrap()
uid, B, DET = get_state()

# ---------- UI helpers ----------
def card(label, value, sub="", color="#e6edf7"):
    st.markdown(f'<div class="card"><div class="l">{label}</div><div class="v" style="color:{color}">{value}</div><div class="s">{sub}</div></div>', unsafe_allow_html=True)

def alert_panel(title, msg, level, ts=""):
    st.markdown(f'<div class="alert" style="border-color:{COLORS[level]}"><b style="color:{COLORS[level]}">{title}</b> '
                f'<span style="color:#8aa0c4;float:right">{ts}</span><br>{msg}</div>', unsafe_allow_html=True)

def gauge(score, level):
    st.markdown(f'<div class="card"><div class="l">Risk score</div><div class="v" style="color:{COLORS[level]}">{score:.0f}/100 · {level}</div>'
                f'<div class="bar"><div style="width:{score}%;background:{COLORS[level]}"></div></div></div>', unsafe_allow_html=True)

def mkfig(w=6, h=3):
    f, ax = plt.subplots(figsize=(w, h)); f.patch.set_facecolor(BG); ax.set_facecolor(BG)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.tick_params(colors="#8aa0c4", labelsize=8); return f, ax

def show(f):
    f.tight_layout(); st.pyplot(f); plt.close(f)

def event_from_row(r):
    return {k: r[k] for k in ("hour", "device", "location", "session_min", "actions", "downloads_mb")}

def twin_vs_reality(e):
    st.markdown("##### Twin vs Reality")
    m = match_percent(e, B)
    c1, c2 = st.columns([2, 1])
    t = compare(e, B)
    with c1: st.dataframe(t, hide_index=True, use_container_width=True)
    with c2: card("Behavioral match", f"{m:.0f}%", f"{(t['Status'] != '✓ Match').sum()} deviation(s) detected", COLORS[level_for(100 - m)])
    f, ax = mkfig(7, 2.6)
    ax.barh(t["Feature"], t["Deviation"], color=["#ef4444" if d >= 2 else "#22c55e" for d in t["Deviation"]])
    ax.axvline(2, ls="--", c="#facc15", lw=1); ax.set_xlabel("Deviation from twin (σ)", color="#8aa0c4"); ax.invert_yaxis(); show(f)

def render_result(e, res):
    gauge(res["score"], res["level"])
    # Continuous verification: risky sessions trigger a step-up challenge, not an automatic verdict
    if res["level"] in ("HIGH RISK", "CRITICAL"): st.error("🔐 Continuous verification: step-up authentication (MFA) required for this session.")
    elif res["level"] == "SUSPICIOUS": st.warning("👁 Session flagged for closer monitoring.")
    if res["alert"]: alert_panel(res["alert"]["title"], res["alert"]["message"], res["level"])
    else: alert_panel("SAFE — Behavior matches Digital Twin", "No action required.", "SAFE")
    twin_vs_reality(e)

DF = load_df(); AL = load_alerts()
last = DF.iloc[-1]

# ---------- sidebar ----------
st.sidebar.markdown("## 🛡️ Digital Twin Guardian")
st.sidebar.caption("AI Identity Behavior Twin")
page = st.sidebar.radio("Navigation", ["Dashboard", "Digital Twin", "Live Monitoring", "Anomaly Detection", "Risk Analysis",
                                       "Attack Simulator", "Security Alerts", "Activity Logs", "Settings"], label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.caption("Monitored identity: **alex.morgan** (Finance Analyst)")
st.sidebar.warning("All behavioral data is SIMULATED for this college prototype.")
st.markdown('<div class="tag">SECURITY OPERATIONS CENTER</div>', unsafe_allow_html=True)
st.title(page)

# ---------- pages ----------
if page == "Dashboard":
    open_al = AL[AL["status"] == "OPEN"]
    c = st.columns(4)
    with c[0]: card("Current risk score", f"{last.score:.0f}", last.level, COLORS[last.level])
    with c[1]: card("Identity confidence", f"{100 - last.score:.0f}%", "inverse of risk", "#00e5ff")
    with c[2]: card("Behavioral match", f"{match_percent(event_from_row(last), B):.0f}%", "latest session vs twin", "#00e5ff")
    with c[3]: card("Active alerts", len(open_al), f"{(open_al['severity'] == 'CRITICAL').sum()} critical", "#fb923c")
    known = B["device"].get(last.device, 0) >= 0.02
    c = st.columns(3)
    with c[0]: card("Anomaly count", int((DF.score > 30).sum()), "sessions scoring above 30", "#facc15")
    with c[1]: card("Device status", "KNOWN" if known else "UNKNOWN", str(last.device), "#22c55e" if known else "#ef4444")
    with c[2]: card("Recent activity", len(DF[DF.ts >= DF.ts.max() - pd.Timedelta(hours=24)]), "sessions in last 24h", "#00e5ff")
    a, b_ = st.columns([2, 1])
    with a:
        st.markdown("##### Anomaly timeline (risk over time)")
        d = DF[DF.ts >= DF.ts.max() - pd.Timedelta(days=12)]
        f, ax = mkfig(8, 3); ax.plot(d.ts, d.score, c="#00e5ff", lw=.8, alpha=.6)
        bad = d[d.score > 30]; ax.scatter(bad.ts, bad.score, c=[COLORS[l] for l in bad.level], s=30, zorder=3)
        for y in (30, 60, 80): ax.axhline(y, ls=":", c="#334155")
        f.autofmt_xdate(); show(f)
    with b_:
        st.markdown("##### Risk distribution")
        v = DF.level.value_counts().reindex(list(COLORS)).fillna(0)
        f, ax = mkfig(3.5, 3); ax.pie(v, labels=v.index, colors=list(COLORS.values()), textprops={"color": "#e6edf7", "fontsize": 7},
                                      wedgeprops={"width": .45}); show(f)
    a, b_, c_ = st.columns(3)
    with a:
        st.markdown("##### Device activity"); f, ax = mkfig(4, 2.5); sns.countplot(data=DF, y="device", ax=ax, color="#00e5ff"); ax.set_ylabel(""); show(f)
    with b_:
        st.markdown("##### Location activity"); f, ax = mkfig(4, 2.5); sns.countplot(data=DF, y="location", ax=ax, color="#8b5cf6"); ax.set_ylabel(""); show(f)
    with c_:
        st.markdown("##### Active alerts")
        for _, r in open_al.head(3).iterrows(): alert_panel(r.title, r.message, r.severity, r.ts.strftime("%d %b %H:%M"))
    st.markdown("##### Recent activities")
    st.dataframe(DF.tail(10).iloc[::-1][["ts", "device", "location", "hour", "session_min", "actions", "downloads_mb", "score", "level"]],
                 hide_index=True, use_container_width=True)

elif page == "Digital Twin":
    st.caption("The twin is learned from this user's historical NORMAL sessions (simulated).")
    c = st.columns(4)
    with c[0]: card("Training sessions", B["n"], "normal behavior only")
    with c[1]: card("Typical login time", f"{B['hour']['mean']:.1f}h", f"± {B['hour']['std']:.1f}h")
    with c[2]: card("Session length", f"{B['session_min']['mean']:.0f} min", f"± {B['session_min']['std']:.0f}")
    with c[3]: card("Avg downloads", f"{B['downloads_mb']['mean']:.0f} MB", f"± {B['downloads_mb']['std']:.0f}")
    a, b_, c_ = st.columns(3)
    nd = DF[DF.label == "normal"]
    with a:
        st.markdown("##### Login-hour pattern"); f, ax = mkfig(4, 2.8); sns.histplot(nd.hour, bins=20, color="#00e5ff", ax=ax); show(f)
    with b_:
        st.markdown("##### Known devices"); f, ax = mkfig(4, 2.8); ax.barh(list(B["device"]), [v * 100 for v in B["device"].values()], color="#22c55e"); ax.set_xlabel("% of sessions", color="#8aa0c4"); show(f)
    with c_:
        st.markdown("##### Known locations"); f, ax = mkfig(4, 2.8); ax.barh(list(B["location"]), [v * 100 for v in B["location"].values()], color="#8b5cf6"); ax.set_xlabel("% of sessions", color="#8aa0c4"); show(f)
    twin_vs_reality(event_from_row(last))

elif page == "Live Monitoring":
    st.caption("Streams simulated sessions through the twin; ~15% are randomly injected attacks.")
    n = st.slider("Events to ingest", 1, 20, 5)
    if st.button("▶ Ingest live events", type="primary"):
        for _ in range(n):
            if random.random() < .15: e = scenario_event(random.choice([k for k in SCENARIOS if k != "normal"]))
            else:
                e = normal_events(1, ts=datetime.now()).iloc[0].to_dict(); e["ts"] = datetime.now()
            record_event(e, uid, B, DET, "live")
        st.rerun()
    for _, r in DF.tail(12).iloc[::-1].iterrows():
        alert_panel(f"{r.level} · {r.score:.0f}/100", f"{r.device} · {r.location} · {r.hour:.1f}h · {r.downloads_mb:.0f} MB", r.level, r.ts.strftime("%d %b %H:%M"))

elif page == "Anomaly Detection":
    st.caption("Isolation Forest (scikit-learn) trained on normal sessions only; higher score = easier to isolate = more abnormal.")
    a, b_ = st.columns(2)
    with a:
        st.markdown("##### Normal vs anomalous behavior"); f, ax = mkfig(5, 3.4)
        sns.scatterplot(data=DF, x="session_min", y="downloads_mb", hue=DF.score.gt(30).map({False: "Normal", True: "Anomalous"}),
                        palette={"Normal": "#22c55e", "Anomalous": "#ef4444"}, ax=ax, s=18); ax.set_yscale("symlog"); show(f)
    with b_:
        st.markdown("##### Anomaly score distribution"); f, ax = mkfig(5, 3.4); sns.histplot(DF.anomaly_score, bins=30, color="#00e5ff", ax=ax); show(f)
    st.markdown("##### Top anomalous events")
    st.dataframe(DF.sort_values("anomaly_score", ascending=False).head(10)[["ts", "device", "location", "hour", "downloads_mb", "anomaly_score", "score", "level"]],
                 hide_index=True, use_container_width=True)

elif page == "Risk Analysis":
    st.caption("Risk = weighted rule-based factors (explainable) + Isolation Forest anomaly score. Max points per factor:")
    a, b_ = st.columns(2)
    with a:
        st.dataframe(pd.DataFrame({"Factor": list(WEIGHTS), "Max points": list(WEIGHTS.values())}), hide_index=True, use_container_width=True)
        st.markdown("##### Behavioral match over time"); f, ax = mkfig(5, 2.6)
        ax.plot(DF.ts.tail(60), [match_percent(event_from_row(r), B) for _, r in DF.tail(60).iterrows()], c="#00e5ff"); ax.set_ylim(0, 105); f.autofmt_xdate(); show(f)
    with b_:
        st.markdown("##### Risk breakdown — latest session")
        e = event_from_row(last); res = compute_risk(e, B, last.anomaly_score)
        fd = pd.DataFrame(res["factors"]); f, ax = mkfig(5, 3); ax.barh(fd.factor, fd.points, color="#fb923c"); ax.invert_yaxis(); show(f)
        gauge(res["score"], res["level"])

elif page == "Attack Simulator":
    st.caption("Pick a scenario; the engine rescoring happens immediately against the Digital Twin.")
    key = st.selectbox("Scenario", list(SCENARIOS), format_func=lambda k: SCENARIOS[k][0])
    st.info(SCENARIOS[key][1])
    c1, c2 = st.columns(2)
    if c1.button("⚡ Run scenario", type="primary"):
        e = scenario_event(key); st.session_state["sim"] = (e, record_event(e, uid, B, DET, "sim"))
    if c2.button("🎬 Run sample account-takeover story"):
        steps = []
        for name, k in SAMPLE_ATTACK:
            e = scenario_event(k); steps.append((name, e, record_event(e, uid, B, DET, "sim")))
        st.session_state["story"] = steps; st.session_state.pop("sim", None)
    if "sim" in st.session_state: render_result(*st.session_state["sim"])
    if "story" in st.session_state:
        steps = st.session_state["story"]
        f, ax = mkfig(7, 2.8); ax.plot(range(1, 6), [s[2]["score"] for s in steps], marker="o", c="#ef4444")
        ax.set_xticks(range(1, 6)); ax.set_ylim(0, 105); ax.set_xlabel("Attack stage", color="#8aa0c4"); ax.set_ylabel("Risk", color="#8aa0c4"); show(f)
        for name, e, res in steps:
            st.markdown(f"**{name}**"); alert_panel(res["alert"]["title"] if res["alert"] else "SAFE — Behavior matches Digital Twin",
                                                    res["alert"]["message"] if res["alert"] else f"Risk Score: {res['score']:.0f}/100", res["level"])

elif page == "Security Alerts":
    sev = st.multiselect("Severity", list(COLORS), default=list(COLORS))
    v = AL[AL.severity.isin(sev)]
    a, b_ = st.columns([2, 1])
    with b_:
        st.markdown("##### Alert severity"); f, ax = mkfig(3.5, 2.8); c = v.severity.value_counts().reindex(list(COLORS)).fillna(0)
        ax.bar(c.index, c.values, color=list(COLORS.values())); plt.setp(ax.get_xticklabels(), rotation=30); show(f)
        if st.button("Mark all as resolved"):
            with engine.begin() as cn: cn.execute(text("UPDATE alerts SET status='RESOLVED'"))
            st.rerun()
    with a:
        for _, r in v.head(25).iterrows(): alert_panel(f"{r.title} [{r.status}]", r.message, r.severity, r.ts.strftime("%d %b %H:%M"))

elif page == "Activity Logs":
    lv = st.multiselect("Risk level", list(COLORS), default=list(COLORS))
    v = DF[DF.level.isin(lv)].iloc[::-1]
    st.dataframe(v.drop(columns=["user_id"]), hide_index=True, use_container_width=True)
    st.download_button("Download CSV", v.to_csv(index=False), "activity_logs.csv")

else:
    st.markdown("##### Risk thresholds")
    st.table(pd.DataFrame({"Range": ["0–30", "31–60", "61–80", "81–100"], "Level": list(COLORS)}))
    st.caption(f"Database: {DB_PATH}")
    if st.button("🔄 Retrain Digital Twin"): st.cache_resource.clear(); st.rerun()
    if st.button("🗑 Reset database & regenerate synthetic data"):
        reset_db(); st.cache_resource.clear(); st.session_state.clear(); st.rerun()
    st.warning("This is an educational prototype. Behavioral data is synthetic; detection quality here does not reflect real-world performance. Isolation Forest flags unusual behavior, not proven malice: a high score should trigger verification, not an automatic accusation. Legitimate users can change habits, and attackers may imitate patterns.")
