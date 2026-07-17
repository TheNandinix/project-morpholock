"""
app.py — MorphoLock Live Dashboard
Final phase 2 version
Author: Nandini (Team Lead)
Run: streamlit run dashboard/app.py
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time
import random
from datetime import datetime
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ── Channel configuration ──
# Maps each banking channel to its real-world transaction format.
# This demonstrates channel-agnostic architecture: the same
# risk engine and HMAC signing pipeline works underneath all four,
# only the presentation layer and nonce format change.
CHANNELS = {
    "UPI": {
        "icon": "📱",
        "nonce_label": "VPA + Amount + Timestamp",
        "id_label": "VPA",
        "id_example": "nandini@upi",
        "sensor_context": "Phone IMU (Android SensorManager / iOS CoreMotion)",
        "key_storage": "ARM TrustZone / Secure Enclave",
        "description": "Real-time peer-to-peer transfer via UPI app"
    },
    "Mobile Banking": {
        "icon": "🏦",
        "nonce_label": "Account ID + Amount + Timestamp",
        "id_label": "Account",
        "id_example": "XXXX-XXXX-4821",
        "sensor_context": "Phone IMU (Android SensorManager / iOS CoreMotion)",
        "key_storage": "ARM TrustZone / Secure Enclave",
        "description": "Fund transfer via bank's native mobile app"
    },
    "Internet Banking": {
        "icon": "💻",
        "nonce_label": "Session ID + Amount + Timestamp",
        "id_label": "Session",
        "id_example": "SESS-88421",
        "sensor_context": "Paired mobile device (cross-device push attestation)",
        "key_storage": "User's phone Secure Enclave",
        "description": "Browser-based transfer, biometric confirmed via paired phone"
    },
    "ATM": {
        "icon": "🏧",
        "nonce_label": "Card Token + Amount + Timestamp",
        "id_label": "Card",
        "id_example": "**** **** **** 7734",
        "sensor_context": "Encrypted PIN Pad (EPP) — embedded IMU",
        "key_storage": "EPP hardware secure module",
        "description": "Cash withdrawal at automated teller machine"
    }
}

# ── Page config — must be first ──
st.set_page_config(
    page_title="MorphoLock",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Lottie — optional, graceful fallback if not installed ──
try:
    from streamlit_lottie import st_lottie
    import requests as _req
    def load_lottie(url):
        try:
            r = _req.get(url, timeout=4)
            return r.json() if r.status_code == 200 else None
        except:
            return None
    LOTTIE_OK = True
except ImportError:
    LOTTIE_OK = False

# ────────────────────────────────────────────
# CSS — The visual identity
# ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #070710;
    color: #E8E6F0;
}
.block-container { padding: 1rem 1.4rem; max-width: 100%; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Particle canvas ── */
#tsparticles {
    position: fixed; top:0; left:0;
    width:100%; height:100%; z-index:0;
    pointer-events:none;
}

/* ── All content above particles ── */
.main .block-container { position: relative; z-index: 1; }

/* ── Header ── */
.ml-header {
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 14px 22px;
    background: rgba(83,74,183,0.07);
    border: 1px solid rgba(83,74,183,0.18);
    border-radius: 14px;
    margin-bottom: 14px;
    position: relative; overflow: hidden;
}
.ml-header::after {
    content:'';
    position:absolute; top:0; left:-60%;
    width:50%; height:100%;
    background: linear-gradient(90deg,transparent,
        rgba(83,74,183,0.07),transparent);
    animation: scan 5s linear infinite;
}
@keyframes scan { 0%{left:-60%} 100%{left:110%} }

.ml-logo {
    font-size: 18px; font-weight: 600;
    color: #E8E6F0; letter-spacing: -0.3px;
    display: flex; align-items: center; gap: 10px;
}
.ml-logo-sub {
    font-size: 11px; font-weight: 400;
    color: rgba(232,230,240,0.35); margin-left: 4px;
}
.live-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(29,158,117,0.1);
    border: 1px solid rgba(29,158,117,0.22);
    border-radius: 20px; padding: 5px 14px;
    font-size: 11px; color: #4ECFA0; font-weight: 500;
}
.live-dot {
    width:7px; height:7px; background:#1D9E75;
    border-radius:50%;
    animation: breathe 2s ease-in-out infinite;
}
@keyframes breathe {
    0%,100%{opacity:1;transform:scale(1)}
    50%{opacity:0.4;transform:scale(0.75)}
}

/* ── Stat cards ── */
.stat-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; padding: 14px 16px;
    text-align: center;
}
.stat-label {
    font-size: 10px; font-weight: 500;
    letter-spacing:.08em; text-transform:uppercase;
    color: rgba(232,230,240,0.3); margin-bottom:6px;
}
.stat-value { font-size:26px; font-weight:500; line-height:1; color:#E8E6F0; }
.stat-sub   { font-size:10px; color:rgba(232,230,240,0.25); margin-top:4px; }

/* ── Section labels ── */
.sec-label {
    font-size:10px; font-weight:500;
    letter-spacing:.08em; text-transform:uppercase;
    color:rgba(232,230,240,0.3); margin-bottom:10px;
}

/* ── Pulse rings around gauge ── */
.gauge-wrap { position:relative; }
.pulse-ring {
    position:absolute; top:50%; left:50%;
    transform:translate(-50%,-50%);
    width:155px; height:155px; border-radius:50%;
    border:1.5px solid rgba(83,74,183,0.35);
    animation:rpulse 3.5s ease-in-out infinite;
    pointer-events:none;
}
.pulse-ring-2 {
    animation-delay:1.75s;
    border-color:rgba(83,74,183,0.15);
    width:180px; height:180px;
}
.pulse-ring-green {
    border-color:rgba(29,158,117,0.35);
    animation-delay:0s;
}
.pulse-ring-red {
    border-color:rgba(255,71,87,0.35);
    animation-delay:0s;
}
@keyframes rpulse {
    0%,100%{transform:translate(-50%,-50%) scale(0.93);opacity:0.85}
    50%{transform:translate(-50%,-50%) scale(1.07);opacity:0.2}
}

/* ── Decision boxes ── */
.dec-approved {
    background:rgba(29,158,117,0.09);
    border:1px solid rgba(29,158,117,0.28);
    border-radius:12px; padding:14px; text-align:center;
}
.dec-blocked {
    background:rgba(255,71,87,0.09);
    border:1px solid rgba(255,71,87,0.28);
    border-radius:12px; padding:14px; text-align:center;
}
.dec-stepup {
    background:rgba(255,179,71,0.09);
    border:1px solid rgba(255,179,71,0.28);
    border-radius:12px; padding:14px; text-align:center;
}
.dec-title { font-size:15px; font-weight:600; margin-bottom:3px; }
.dec-sub   { font-size:11px; color:rgba(232,230,240,0.4); }

/* ── Threat tags ── */
.threat-clear {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(29,158,117,0.09);
    border:1px solid rgba(29,158,117,0.2);
    border-radius:8px; padding:6px 12px;
    font-size:11px; color:#4ECFA0;
}
.threat-found {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(255,71,87,0.09);
    border:1px solid rgba(255,71,87,0.2);
    border-radius:8px; padding:6px 12px;
    font-size:11px; color:#FF6B7A;
}

/* ── Log lines ── */
.log-wrap {
    height:190px; overflow-y:auto;
    background:rgba(0,0,0,0.2);
    border-radius:10px; padding:10px 12px;
}
.log-line {
    font-family:'Courier New',monospace;
    font-size:10.5px; padding:2px 0;
    border-bottom:1px solid rgba(255,255,255,0.03);
    color:rgba(232,230,240,0.45); line-height:1.7;
}
.log-ok   { color:#4ECFA0; }
.log-warn { color:#FFB347; }
.log-err  { color:#FF6B7A; }

/* ── Txn rows ── */
.txn-row {
    display:flex; justify-content:space-between;
    padding:6px 0;
    border-bottom:1px solid rgba(255,255,255,0.05);
    font-size:11px;
}
.txn-key { color:rgba(232,230,240,0.35); }
.txn-val { font-family:monospace; color:#E8E6F0; }

/* ── Component bars ── */
.cb-wrap {
    background:rgba(255,255,255,0.06);
    border-radius:20px; height:4px;
    overflow:hidden; margin:3px 0 6px;
}
.cb-fill { height:100%; border-radius:20px; transition:width .7s ease; }
</style>

<!-- Particle background -->
<script src="https://cdn.jsdelivr.net/npm/tsparticles@2/tsparticles.bundle.min.js"></script>
<div id="tsparticles"></div>
<script>
document.addEventListener("DOMContentLoaded", function() {
    if(typeof tsParticles !== 'undefined') {
        tsParticles.load("tsparticles", {
            particles: {
                number: { value: 40 },
                color:  { value: "#534AB7" },
                opacity:{ value: 0.12, random: true },
                size:   { value: 1.8 },
                move:   { enable:true, speed:0.35 },
                links:  {
                    enable:true, color:"#534AB7",
                    opacity:0.07, distance:110
                }
            },
            background:{ color:"transparent" }
        });
    }
});
</script>
""", unsafe_allow_html=True)


# ────────────────────────────────────────────
# SESSION STATE
# ────────────────────────────────────────────
defaults = {
    'txn_count':    0,
    'approved':     0,
    'blocked':      0,
    'log_lines':    [],
    'last_result':  None,
    'risk_history': []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────
def add_log(msg: str, level: str = "info"):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_lines.append(
        {"ts": ts, "msg": msg, "level": level}
    )
    st.session_state.log_lines = st.session_state.log_lines[-14:]


def gen_tremor(human: bool = True) -> np.ndarray:
    t = np.linspace(0, 2, 200)
    if human:
        return (
            0.09 * np.sin(2*np.pi*10*t) +
            0.03 * np.sin(2*np.pi*8.5*t) +
            0.02 * np.sin(2*np.pi*11.2*t) +
            0.008 * np.random.randn(200)
        )
    return 0.002 * np.random.randn(200)


def real_tremor_signal(sensor_window) -> np.ndarray:
    """
    Builds a single 1D wave from REAL captured Ax,Ay,Az data, purely
    for the on-screen graph. This is NOT used for risk scoring —
    that still happens per-axis in ml_pipeline/signal_processor.py.
    We remove each axis's average (gravity / steady tilt) so the
    small tremor oscillation is visible instead of being flattened
    by the constant ~1g offset on the Z-axis.
    """
    data = np.array(sensor_window, dtype=float)
    accel = data[:, :3]
    accel_ac = accel - accel.mean(axis=0)
    mag = np.sqrt(np.sum(accel_ac ** 2, axis=1))
    return mag - mag.mean()


def fft_spectrum(sig: np.ndarray):
    n = len(sig)
    fv = np.abs(np.fft.rfft(sig))
    fr = np.fft.rfftfreq(n, d=1/100)
    fv = fv / (fv.max() + 1e-10)
    return fr, fv


def sim_txn(mode: str) -> dict:
    if mode == "human":
        rs = random.randint(11, 27)
        dec = "APPROVED"
        sig = gen_tremor(True)
        th  = []
        cr  = 0
    elif mode == "attack":
        rs = random.randint(76, 95)
        dec = "BLOCKED"
        sig = gen_tremor(False)
        th  = []
        cr  = 0
    else:
        rs = random.randint(72, 88)
        dec = "BLOCKED"
        sig = gen_tremor(True)
        th  = ["AnyDesk"]
        cr  = 40

    tr = max(0, min(50, rs - int(cr/2)))
    return {
        "risk_score":     rs,
        "decision":       dec,
        "tremor_signal":  sig,
        "threats":        th,
        "transaction_id": f"TXN{random.randint(100,999)}",
        "amount":         random.choice([1000,2500,5000,10000,25000]),
        "token":          ''.join(random.choices('0123456789abcdef',k=16))+"...",
        "components": {
            "tremor_risk":  tr,
            "context_risk": cr,
            "tilt_risk":    random.randint(0,3)
        }
    }


# ────────────────────────────────────────────
# CHARTS
# ────────────────────────────────────────────
def fft_chart(sig: np.ndarray, decision: str) -> go.Figure:
    fr, sp = fft_spectrum(sig)
    approved = decision == "APPROVED"
    lc = "#534AB7" if approved else "#FF4757"
    fc = "rgba(83,74,183,0.13)" if approved else "rgba(255,71,87,0.13)"
    bc = "rgba(83,74,183,0.07)" if approved else "rgba(255,71,87,0.07)"

    fig = go.Figure()
    fig.add_shape(type="rect", x0=8, x1=12, y0=0, y1=1.05,
                  fillcolor=bc,
                  line=dict(color=lc, width=0.8, dash="dot"),
                  layer="below")
    fig.add_trace(go.Scatter(
        x=fr, y=sp, mode="lines",
        line=dict(color=lc, width=1.8, shape="spline"),
        fill="tozeroy", fillcolor=fc,
        hovertemplate="<b>%{x:.1f} Hz</b><br>Power: %{y:.3f}<extra></extra>"
    ))
    fig.add_annotation(x=10, y=1.04,
        text="8–12 Hz  biological tremor band",
        showarrow=False,
        font=dict(size=9.5, color=lc), xanchor="center")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor ="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=16,b=28), height=155,
        xaxis=dict(range=[0,25], color="rgba(232,230,240,0.25)",
                   showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=9), title="Frequency (Hz)",
                   title_font=dict(size=9)),
        yaxis=dict(range=[0,1.1], color="rgba(232,230,240,0.25)",
                   showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=9)),
        showlegend=False
    )
    return fig


def gauge_chart(score: int) -> go.Figure:
    if score < 30:
        color = "#1D9E75"
    elif score < 70:
        color = "#FFB347"
    else:
        color = "#FF4757"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(size=38, color="#E8E6F0",
                              family="Inter"), suffix=""),
        gauge=dict(
            axis=dict(range=[0,100],
                      tickcolor="rgba(232,230,240,0.15)",
                      tickfont=dict(size=9,
                                    color="rgba(232,230,240,0.25)"),
                      dtick=25),
            bar=dict(color=color, thickness=0.22),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            steps=[
                dict(range=[0,30],  color="rgba(29,158,117,0.07)"),
                dict(range=[30,70], color="rgba(255,179,71,0.07)"),
                dict(range=[70,100],color="rgba(255,71,87,0.07)")
            ],
            threshold=dict(
                line=dict(color=color, width=2),
                thickness=0.82, value=score)
        )
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor ="rgba(0,0,0,0)",
        margin=dict(l=10,r=10,t=8,b=0),
        height=175,
        font=dict(family="Inter", color="#E8E6F0")
    )
    return fig


def history_chart(hist: list) -> go.Figure:
    if not hist:
        hist = [0]
    colors = ["#1D9E75" if s<30 else "#FFB347" if s<70
              else "#FF4757" for s in hist]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(range(len(hist))), y=hist,
        marker_color=colors,
        hovertemplate="Txn %{x}<br>Risk: %{y}<extra></extra>"
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor ="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=0,b=0), height=75,
        xaxis=dict(visible=False),
        yaxis=dict(range=[0,100],
                   color="rgba(232,230,240,0.2)",
                   tickfont=dict(size=8),
                   gridcolor="rgba(255,255,255,0.04)"),
        showlegend=False
    )
    return fig


# ────────────────────────────────────────────
# PROCESS TRANSACTION RESULT → dashboard format
# ────────────────────────────────────────────
def process_result(result: dict, mode: str):
    human = result["decision"] != "BLOCKED"
    real_window = result.get("sensor_window")
    if real_window:
        tremor_signal = real_tremor_signal(real_window)
    else:
        tremor_signal = gen_tremor(human)
    dr = {
        "risk_score":     result["risk_score"],
        "decision":       result["decision"],
        "tremor_signal":  tremor_signal,
        "threats":        result.get("components",{}).get("threats",
                          result.get("threats",[])),
        "transaction_id": result.get("transaction_id","TXN_LIVE"),
        "amount":         result.get("amount", 5000),
        "token":          result.get("token","N/A"),
        "components":     result.get("components",{
                              "tremor_risk":50,
                              "context_risk":0,
                              "tilt_risk":0
                          })
    }
    st.session_state.last_result = dr
    st.session_state.txn_count  += 1
    st.session_state.risk_history.append(result["risk_score"])
    if result["decision"] == "APPROVED":
        st.session_state.approved += 1
    else:
        st.session_state.blocked  += 1


# ────────────────────────────────────────────
# MAIN RENDER
# ────────────────────────────────────────────
def render():
    r = st.session_state.last_result

    # ── HEADER ──
    hcol1, hcol2 = st.columns([1, 10])
    with hcol1:
        if LOTTIE_OK:
            ld = load_lottie(
                "https://assets5.lottiefiles.com/packages/lf20_ystsffqy.json")
            if ld:
                st_lottie(ld, height=52, width=52,
                          key="shield", speed=0.7)
    with hcol2:
        st.markdown(f"""
        <div class="ml-header">
          <div class="ml-logo">🔐 MorphoLock
            <span class="ml-logo-sub">
              Behavioral Attestation Framework &nbsp;·&nbsp; MNNIT Hackathon 2026
            </span>
          </div>
          <div style="display:flex;align-items:center;gap:14px">
            <span style="font-size:11px;color:rgba(232,230,240,0.25)">
              {datetime.now().strftime("%d %b %Y &nbsp; %H:%M:%S")}
            </span>
            <div class="live-pill">
              <div class="live-dot"></div>System Active
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    # ── Channel selector ──
    st.markdown('<div class="sec-label" style="margin-top:4px">'
                'Banking channel</div>', unsafe_allow_html=True)

    chan_cols = st.columns(4)
    if 'selected_channel' not in st.session_state:
        st.session_state.selected_channel = "UPI"

    for i, ch_name in enumerate(CHANNELS.keys()):
        with chan_cols[i]:
            ch = CHANNELS[ch_name]
            is_active = st.session_state.selected_channel == ch_name
            if st.button(
                f"{ch['icon']}  {ch_name}",
                key=f"chan_{ch_name}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.selected_channel = ch_name
                st.rerun()

    active_channel = CHANNELS[st.session_state.selected_channel]
    st.markdown(f"""
    <div style="font-size:10px;color:rgba(232,230,240,0.35);
                margin:4px 0 10px;padding:8px 12px;
                background:rgba(255,255,255,0.02);
                border-radius:8px;line-height:1.6">
        <b>{st.session_state.selected_channel}:</b> {active_channel['description']}
        &nbsp;·&nbsp; Sensor: {active_channel['sensor_context']}
        &nbsp;·&nbsp; Key storage: {active_channel['key_storage']}
    </div>
    """, unsafe_allow_html=True)
    # ── STAT BAR ──
    tc = st.session_state.txn_count
    ap = st.session_state.approved
    bl = st.session_state.blocked
    rh = st.session_state.risk_history
    ar = round(ap/tc*100) if tc else 0
    avg= round(np.mean(rh)) if rh else 0

    s1,s2,s3,s4 = st.columns(4)
    for col, label, val, sub, color in [
        (s1, "Transactions",  tc,  "This session",         "#E8E6F0"),
        (s2, "Approved",      ap,  f"{ar}% approval rate", "#4ECFA0"),
        (s3, "Blocked",       bl,  "Attacks caught",       "#FF6B7A"),
        (s4, "Avg risk score",avg, "Session average",      "#E8E6F0"),
    ]:
        with col:
            st.markdown(f"""
            <div class="stat-card">
              <div class="stat-label">{label}</div>
              <div class="stat-value" style="color:{color}">{val}</div>
              <div class="stat-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:6px'></div>",
                unsafe_allow_html=True)

    # ── MAIN COLUMNS ──
    left, right = st.columns([2.2, 1], gap="medium")

    with left:
        # FFT graph
        st.markdown('<div class="sec-label">Live tremor spectrum — FFT analysis</div>',
                    unsafe_allow_html=True)
        sig  = r["tremor_signal"] if r else gen_tremor(True)
        dec  = r["decision"]      if r else "APPROVED"
        st.plotly_chart(fft_chart(sig, dec),
                        use_container_width=True,
                        config={"displayModeBar":False})

        # Risk history
        if rh:
            st.markdown('<div class="sec-label" '
                        'style="margin-top:2px">'
                        'Risk score history</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(history_chart(rh[-10:]),
                            use_container_width=True,
                            config={"displayModeBar":False})

        # Transaction details
        if r:
            st.markdown('<div class="sec-label" '
                        'style="margin-top:4px">'
                        'Transaction details</div>',
                        unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f"""
                <div class="txn-row">
                  <span class="txn-key">Transaction ID</span>
                  <span class="txn-val">{r['transaction_id']}</span>
                </div>
                <div class="txn-row">
                  <span class="txn-key">Amount</span>
                  <span class="txn-val">₹{r['amount']:,}</span>
                </div>
                <div class="txn-row">
                  <span class="txn-key">Token</span>
                  <span class="txn-val"
                    style="font-size:10px">{r['token']}</span>
                </div>
                <div class="txn-row">
                  <span class="txn-key">Timestamp</span>
                  <span class="txn-val">
                    {datetime.now().strftime('%H:%M:%S')}
                  </span>
                </div>
                """, unsafe_allow_html=True)
            with d2:
                comp = r["components"]
                for nm, val, mx, clr in [
                    ("Tremor",  comp.get("tremor_risk",0),  50, "#534AB7"),
                    ("Context", comp.get("context_risk",0), 40, "#1D9E75"),
                    ("Tilt",    comp.get("tilt_risk",0),    10, "#D85A30"),
                ]:
                    pct = int(val/mx*100)
                    st.markdown(f"""
                    <div style="margin-bottom:7px">
                      <div style="display:flex;justify-content:space-between;
                          font-size:10px;color:rgba(232,230,240,0.35);
                          margin-bottom:2px">
                        <span>{nm}</span><span>{val}/{mx}</span>
                      </div>
                      <div class="cb-wrap">
                        <div class="cb-fill"
                          style="width:{pct}%;background:{clr}">
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)

            # Threat status
            if r["threats"]:
                st.markdown(f"""<div class="threat-found">
                  ⚠ &nbsp;Threats: {', '.join(r['threats'])}
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div class="threat-clear">
                  ✓ &nbsp;Environment clear — no screen-sharing detected
                </div>""", unsafe_allow_html=True)

    with right:
        # Gauge with pulse rings
        st.markdown('<div class="sec-label">Risk score</div>',
                    unsafe_allow_html=True)
        score = r["risk_score"] if r else 0
        ring_class = ("pulse-ring-green" if score < 30
                      else "pulse-ring-red" if score >= 70
                      else "")
        st.markdown(f"""
        <div class="gauge-wrap">
          <div class="pulse-ring {ring_class}"></div>
          <div class="pulse-ring pulse-ring-2 {ring_class}"></div>
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(gauge_chart(score),
                        use_container_width=True,
                        config={"displayModeBar":False})

        # Decision box
        if r:
            d = r["decision"]
            if d == "APPROVED":
                st.markdown("""<div class="dec-approved">
                  <div class="dec-title" style="color:#4ECFA0">
                    ✓ &nbsp;Transaction Approved</div>
                  <div class="dec-sub">HMAC token verified by bank</div>
                </div>""", unsafe_allow_html=True)
            elif d == "BLOCKED":
                st.markdown("""<div class="dec-blocked">
                  <div class="dec-title" style="color:#FF6B7A">
                    ✗ &nbsp;Transaction Blocked</div>
                  <div class="dec-sub">High risk — rejected</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div class="dec-stepup">
                  <div class="dec-title" style="color:#FFB347">
                    ⚡ &nbsp;Step-up Required</div>
                  <div class="dec-sub">Additional verification needed</div>
                </div>""", unsafe_allow_html=True)

        # System log
        st.markdown('<div class="sec-label" '
                    'style="margin-top:14px">System log</div>',
                    unsafe_allow_html=True)
        log_html = ""
        for ln in reversed(
                st.session_state.log_lines[-12:]):
            css = {"success":"log-ok",
                   "warning":"log-warn",
                   "error":"log-err"}.get(ln["level"],"")
            log_html += (
                f'<div class="log-line {css}">'
                f'<span style="color:rgba(232,230,240,0.2)">'
                f'{ln["ts"]}</span>&nbsp;&nbsp;{ln["msg"]}</div>'
            )
        st.markdown(
            f'<div class="log-wrap">{log_html}</div>',
            unsafe_allow_html=True)

    # ── DEMO CONTROLS ──
    st.markdown("<div style='margin-top:10px'></div>",
                unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div class="sec-label">Demo controls</div>',
                unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)

    with b1:
        if st.button("✋  Human transaction",
                     use_container_width=True):
            res = sim_txn("human")
            process_result(res, "human")
            add_log("Transaction initiated", "info")
            add_log("200 samples collected at 100Hz", "info")
            add_log(f"FFT — peak at ~10Hz detected", "info")
            add_log(f"Tremor match: CONFIRMED", "info")
            add_log("Environment: CLEAR", "info")
            add_log(f"Risk score: {res['risk_score']}/100", "info")
            add_log("APPROVED — HMAC token generated ✓", "success")
            st.rerun()

    with b2:
        if st.button("💻  Replay attack",
                     use_container_width=True):
            res = sim_txn("attack")
            process_result(res, "attack")
            add_log("Transaction initiated", "info")
            add_log("Data received from pipeline", "info")
            add_log("FFT — 0Hz flat signal (no tremor)", "warning")
            add_log("Hardware idle — no human contact", "warning")
            add_log(f"Risk score: {res['risk_score']}/100", "warning")
            add_log("BLOCKED — software replay detected ✗", "error")
            st.rerun()

    with b3:
        if st.button("📡  Screen-share threat",
                     use_container_width=True):
            res = sim_txn("threat")
            process_result(res, "threat")
            add_log("Transaction initiated", "info")
            add_log("200 samples collected", "info")
            add_log("Tremor detected — human present", "info")
            add_log("THREAT: AnyDesk active — APP scam", "error")
            add_log(f"Risk score: {res['risk_score']}/100", "warning")
            add_log("BLOCKED — screen-share detected ✗", "error")
            st.rerun()

    with b4:
        if st.button("🔴  Live sensor",
                     use_container_width=True,
                     type="primary"):
            with st.spinner(
                    "Hold the sensor... reading 2 seconds"):
                try:
                    from dashboard.main_pipeline import (
                        run_transaction)
                    res = run_transaction("TXN_LIVE", 5000.0)
                    process_result(res, "live")
                    add_log("LIVE hardware transaction", "info")
                    add_log(
                        f"Decision: {res['decision']}",
                        "success" if res["decision"] == "APPROVED"
                        else "error")
                    st.rerun()
                except Exception as e:
                    add_log(f"Hardware error: {str(e)}", "error")
                    st.rerun()


render()