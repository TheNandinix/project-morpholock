"""
app.py — MorphoLock Live Dashboard
===================================
The visual centrepiece of the entire system.
Built with Streamlit. Shows live tremor spectrum,
risk score, transaction details, and system log.

Author: Nandini (Team Lead)
Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time
import random
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ─────────────────────────────────────────────────────
# PAGE CONFIGURATION — must be first Streamlit command
# ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="MorphoLock",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────
# CUSTOM CSS — the visual identity of the dashboard
# This is what makes it look premium and alive
# ─────────────────────────────────────────────────────
st.markdown("""
<style>
/* Import clean font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

/* Base styles */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0A0A0F;
    color: #E8E6F0;
}

/* Remove Streamlit default padding */
.block-container {
    padding: 1.2rem 1.5rem 1rem 1.5rem;
    max-width: 100%;
}

/* Hide default Streamlit menu and footer */
#MainMenu, footer, header {visibility: hidden;}

/* ── Cards ── */
.ml-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 12px;
    backdrop-filter: blur(10px);
}

/* ── Header ── */
.ml-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 22px;
    background: rgba(83, 74, 183, 0.08);
    border: 1px solid rgba(83, 74, 183, 0.2);
    border-radius: 14px;
    margin-bottom: 16px;
}
.ml-logo {
    font-size: 20px;
    font-weight: 600;
    color: #E8E6F0;
    letter-spacing: -0.3px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.ml-logo-sub {
    font-size: 12px;
    font-weight: 400;
    color: rgba(232,230,240,0.4);
    margin-left: 4px;
}
.live-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(29, 158, 117, 0.12);
    border: 1px solid rgba(29, 158, 117, 0.25);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 12px;
    color: #4ECFA0;
    font-weight: 500;
}
.live-dot {
    width: 7px; height: 7px;
    background: #1D9E75;
    border-radius: 50%;
    animation: breathe 2s ease-in-out infinite;
}
@keyframes breathe {
    0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 0 rgba(29,158,117,0.4); }
    50% { opacity: 0.6; transform: scale(0.85); box-shadow: 0 0 0 4px rgba(29,158,117,0); }
}

/* ── Stat cards ── */
.stat-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 14px 18px;
    text-align: center;
}
.stat-label {
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(232,230,240,0.35);
    margin-bottom: 6px;
}
.stat-value {
    font-size: 28px;
    font-weight: 500;
    line-height: 1;
    color: #E8E6F0;
}
.stat-sub {
    font-size: 10px;
    color: rgba(232,230,240,0.3);
    margin-top: 4px;
}

/* ── Section labels ── */
.section-label {
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(232,230,240,0.35);
    margin-bottom: 12px;
}

/* ── Decision box ── */
.decision-approved {
    background: rgba(29, 158, 117, 0.1);
    border: 1px solid rgba(29, 158, 117, 0.3);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.decision-blocked {
    background: rgba(220, 53, 69, 0.1);
    border: 1px solid rgba(220, 53, 69, 0.3);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.decision-stepup {
    background: rgba(255, 165, 0, 0.1);
    border: 1px solid rgba(255, 165, 0, 0.3);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.decision-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
}
.decision-sub {
    font-size: 11px;
    color: rgba(232,230,240,0.5);
}

/* ── Threat tag ── */
.threat-clear {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(29,158,117,0.1);
    border: 1px solid rgba(29,158,117,0.2);
    border-radius: 8px; padding: 6px 12px;
    font-size: 11px; color: #4ECFA0;
}
.threat-found {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(220,53,69,0.1);
    border: 1px solid rgba(220,53,69,0.2);
    border-radius: 8px; padding: 6px 12px;
    font-size: 11px; color: #FF6B7A;
}

/* ── Log lines ── */
.log-line {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 11px;
    padding: 3px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    color: rgba(232,230,240,0.55);
    line-height: 1.6;
}
.log-success { color: #4ECFA0; }
.log-warning { color: #FFB347; }
.log-error   { color: #FF6B7A; }

/* ── Component bars ── */
.comp-bar-wrap {
    background: rgba(255,255,255,0.06);
    border-radius: 20px;
    height: 5px;
    overflow: hidden;
    margin: 4px 0 6px;
}
.comp-bar-fill {
    height: 100%;
    border-radius: 20px;
    transition: width 0.6s ease;
}

/* ── Txn row ── */
.txn-row {
    display: flex;
    justify-content: space-between;
    padding: 7px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    font-size: 12px;
}
.txn-key { color: rgba(232,230,240,0.4); }
.txn-val { font-family: monospace; color: #E8E6F0; }

/* Plotly chart background */
.js-plotly-plot .plotly {
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────
# SESSION STATE — persists across reruns
# Like memory for a single session
# ─────────────────────────────────────────────────────
if 'transaction_count'  not in st.session_state:
    st.session_state.transaction_count  = 0
if 'approved_count'     not in st.session_state:
    st.session_state.approved_count     = 0
if 'blocked_count'      not in st.session_state:
    st.session_state.blocked_count      = 0
if 'log_lines'          not in st.session_state:
    st.session_state.log_lines          = []
if 'last_result'        not in st.session_state:
    st.session_state.last_result        = None
if 'risk_history'       not in st.session_state:
    st.session_state.risk_history       = []


# ─────────────────────────────────────────────────────
# HELPER — generate fake tremor waveform for demo
# When hardware is not connected — shows realistic data
# When hardware IS connected — this gets replaced by real data
# ─────────────────────────────────────────────────────
def generate_demo_tremor(is_human: bool = True) -> np.ndarray:
    """
    Generates a realistic-looking tremor signal for demo.
    Human = has 8-12 Hz component. Flat = near zero.
    """
    t = np.linspace(0, 2, 200)  # 2 seconds, 200 points
    if is_human:
        # Real human tremor: dominant 8-12Hz + small noise
        signal = (
            0.08 * np.sin(2 * np.pi * 10 * t) +   # 10Hz tremor
            0.03 * np.sin(2 * np.pi * 8.5 * t) +  # 8.5Hz component
            0.02 * np.sin(2 * np.pi * 11.5 * t) + # 11.5Hz component
            0.01 * np.random.randn(200)             # small noise
        )
    else:
        # Flat device — near zero signal
        signal = 0.002 * np.random.randn(200)
    return signal


def compute_fft_spectrum(signal: np.ndarray, sample_rate: int = 100):
    """Converts raw signal into frequency spectrum using FFT."""
    n = len(signal)
    fft_vals = np.abs(np.fft.rfft(signal))
    freqs    = np.fft.rfftfreq(n, d=1.0/sample_rate)
    # Normalize to 0-1 scale
    fft_vals = fft_vals / (fft_vals.max() + 1e-10)
    return freqs, fft_vals


def add_log(message: str, level: str = "info"):
    """Add a line to the system log with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_lines.append({
        "time": timestamp,
        "msg":  message,
        "level": level
    })
    # Keep only last 12 log lines
    if len(st.session_state.log_lines) > 12:
        st.session_state.log_lines = st.session_state.log_lines[-12:]


def simulate_transaction(mode: str) -> dict:
    """
    Simulates a full transaction for demo purposes.
    mode: 'human' | 'attack' | 'threat'
    """
    if mode == "human":
        risk_score = random.randint(12, 28)
        decision   = "APPROVED"
        tremor     = generate_demo_tremor(True)
        threats    = []
    elif mode == "attack":
        risk_score = random.randint(78, 96)
        decision   = "BLOCKED"
        tremor     = generate_demo_tremor(False)
        threats    = []
    else:  # threat — AnyDesk running
        risk_score = random.randint(72, 90)
        decision   = "BLOCKED"
        tremor     = generate_demo_tremor(True)
        threats    = ["AnyDesk"]

    return {
        "risk_score":     risk_score,
        "decision":       decision,
        "tremor_signal":  tremor,
        "threats":        threats,
        "transaction_id": f"TXN{random.randint(100,999)}",
        "amount":         random.choice([1000, 2500, 5000, 10000, 25000]),
        "token":          ''.join(random.choices('0123456789abcdef', k=16)) + "...",
        "components": {
            "tremor_risk":  int(risk_score * 0.5) if mode != "attack" else 50,
            "context_risk": 40 if threats else 0,
            "tilt_risk":    random.randint(0, 3)
        }
    }


# ─────────────────────────────────────────────────────
# FFT CHART — the live tremor spectrum graph
# ─────────────────────────────────────────────────────
def build_fft_chart(signal: np.ndarray, decision: str) -> go.Figure:
    freqs, spectrum = compute_fft_spectrum(signal)

    # Color based on decision
    line_color = "#534AB7" if decision == "APPROVED" else "#FF6B7A"
    fill_color = "rgba(83,74,183,0.15)" if decision == "APPROVED" else "rgba(255,107,122,0.15)"
    band_color = "rgba(83,74,183,0.08)" if decision == "APPROVED" else "rgba(255,107,122,0.08)"

    fig = go.Figure()

    # Highlight the 8-12Hz biological tremor band
    fig.add_shape(
        type="rect",
        x0=8, x1=12, y0=0, y1=1.05,
        fillcolor=band_color,
        line=dict(color=line_color, width=0.5, dash="dot"),
        layer="below"
    )

    # The FFT spectrum line
    fig.add_trace(go.Scatter(
        x=freqs,
        y=spectrum,
        mode="lines",
        line=dict(color=line_color, width=1.8, shape="spline"),
        fill="tozeroy",
        fillcolor=fill_color,
        hovertemplate="<b>%{x:.1f} Hz</b><br>Power: %{y:.3f}<extra></extra>"
    ))

    # Label the tremor band
    fig.add_annotation(
        x=10, y=1.02,
        text="8–12 Hz  biological band",
        showarrow=False,
        font=dict(size=10, color=line_color),
        xanchor="center"
    )

    fig.update_layout(
        plot_bgcolor  = "rgba(0,0,0,0)",
        paper_bgcolor = "rgba(0,0,0,0)",
        margin        = dict(l=0, r=0, t=10, b=30),
        height        = 160,
        xaxis=dict(
            title     = "Frequency (Hz)",
            range     = [0, 25],
            color     = "rgba(232,230,240,0.3)",
            showgrid  = True,
            gridcolor = "rgba(255,255,255,0.04)",
            tickfont  = dict(size=10),
            title_font= dict(size=10)
        ),
        yaxis=dict(
            range     = [0, 1.1],
            color     = "rgba(232,230,240,0.3)",
            showgrid  = True,
            gridcolor = "rgba(255,255,255,0.04)",
            tickfont  = dict(size=10)
        ),
        showlegend = False
    )
    return fig


# ─────────────────────────────────────────────────────
# GAUGE CHART — the risk score dial
# ─────────────────────────────────────────────────────
def build_gauge(risk_score: int) -> go.Figure:
    if risk_score < 30:
        color = "#1D9E75"
        label = "Safe zone"
    elif risk_score < 70:
        color = "#FFB347"
        label = "Caution zone"
    else:
        color = "#FF4757"
        label = "Danger zone"

    fig = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = risk_score,
        number= dict(
            font=dict(size=36, color="#E8E6F0", family="Inter"),
            suffix=""
        ),
        gauge = dict(
            axis=dict(
                range    = [0, 100],
                tickcolor= "rgba(232,230,240,0.2)",
                tickfont = dict(size=9, color="rgba(232,230,240,0.3)"),
                dtick    = 25
            ),
            bar=dict(
                color    = color,
                thickness= 0.25
            ),
            bgcolor   = "rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            steps=[
                dict(range=[0,  30], color="rgba(29,158,117,0.08)"),
                dict(range=[30, 70], color="rgba(255,179,71,0.08)"),
                dict(range=[70,100], color="rgba(255,71,87,0.08)")
            ],
            threshold=dict(
                line=dict(color=color, width=2),
                thickness=0.8,
                value=risk_score
            )
        )
    ))

    fig.update_layout(
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
        margin        = dict(l=10, r=10, t=10, b=0),
        height        = 170,
        font          = dict(family="Inter", color="#E8E6F0")
    )
    return fig


# ─────────────────────────────────────────────────────
# RISK HISTORY CHART — sparkline of last 10 scores
# ─────────────────────────────────────────────────────
def build_history_chart(history: list) -> go.Figure:
    if not history:
        history = [0]
    x = list(range(len(history)))
    colors = ["#1D9E75" if s < 30 else "#FFB347" if s < 70 else "#FF4757" for s in history]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=history,
        marker_color=colors,
        hovertemplate="Transaction %{x}<br>Risk: %{y}<extra></extra>"
    ))
    fig.update_layout(
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
        margin        = dict(l=0, r=0, t=0, b=0),
        height        = 80,
        xaxis=dict(visible=False),
        yaxis=dict(
            range=[0, 100],
            color="rgba(232,230,240,0.2)",
            tickfont=dict(size=8),
            gridcolor="rgba(255,255,255,0.04)"
        ),
        showlegend=False
    )
    return fig


# ─────────────────────────────────────────────────────
# MAIN DASHBOARD LAYOUT
# ─────────────────────────────────────────────────────
def render_dashboard():

    # ── HEADER ──
    st.markdown(f"""
    <div class="ml-header">
        <div class="ml-logo">
            🔐 MorphoLock
            <span class="ml-logo-sub">Behavioral Attestation Framework · MNNIT Hackathon 2026</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
            <span style="font-size:11px;color:rgba(232,230,240,0.3)">
                {datetime.now().strftime("%d %b %Y  %H:%M:%S")}
            </span>
            <div class="live-pill">
                <div class="live-dot"></div>
                System Active
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── STAT BAR ──
    approval_rate = (
        round(st.session_state.approved_count /
              st.session_state.transaction_count * 100)
        if st.session_state.transaction_count > 0 else 0
    )
    avg_risk = (
        round(np.mean(st.session_state.risk_history))
        if st.session_state.risk_history else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-label">Transactions</div>
            <div class="stat-value">{st.session_state.transaction_count}</div>
            <div class="stat-sub">This session</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-label">Approved</div>
            <div class="stat-value" style="color:#4ECFA0">{st.session_state.approved_count}</div>
            <div class="stat-sub">{approval_rate}% approval rate</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-label">Blocked</div>
            <div class="stat-value" style="color:#FF6B7A">{st.session_state.blocked_count}</div>
            <div class="stat-sub">Attacks caught</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-label">Avg risk score</div>
            <div class="stat-value">{avg_risk}</div>
            <div class="stat-sub">Session average</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)

    # ── MAIN CONTENT ──
    left, right = st.columns([2, 1], gap="medium")

    with left:

        # FFT spectrum card
        st.markdown('<div class="section-label">Live tremor spectrum — FFT analysis</div>',
                    unsafe_allow_html=True)

        result = st.session_state.last_result
        if result:
            signal   = result["tremor_signal"]
            decision = result["decision"]
        else:
            signal   = generate_demo_tremor(True)
            decision = "APPROVED"

        st.plotly_chart(
            build_fft_chart(signal, decision),
            use_container_width=True,
            config={"displayModeBar": False}
        )

        # Risk score history sparkline
        if st.session_state.risk_history:
            st.markdown('<div class="section-label" style="margin-top:4px">Risk score history — last 10 transactions</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(
                build_history_chart(st.session_state.risk_history[-10:]),
                use_container_width=True,
                config={"displayModeBar": False}
            )

        # Transaction details
        if result:
            st.markdown('<div class="section-label" style="margin-top:4px">Transaction details</div>',
                        unsafe_allow_html=True)

            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f"""
                <div class="txn-row"><span class="txn-key">Transaction ID</span>
                    <span class="txn-val">{result['transaction_id']}</span></div>
                <div class="txn-row"><span class="txn-key">Amount</span>
                    <span class="txn-val">₹{result['amount']:,}</span></div>
                <div class="txn-row"><span class="txn-key">Token</span>
                    <span class="txn-val" style="font-size:10px">{result['token']}</span></div>
                """, unsafe_allow_html=True)
            with d2:
                comp = result["components"]
                for name, val, maxval, color in [
                    ("Tremor",  comp["tremor_risk"],  50, "#534AB7"),
                    ("Context", comp["context_risk"], 40, "#1D9E75"),
                    ("Tilt",    comp["tilt_risk"],    10, "#D85A30")
                ]:
                    pct = int(val / maxval * 100)
                    st.markdown(f"""
                    <div style="margin-bottom:8px">
                        <div style="display:flex;justify-content:space-between;
                            font-size:10px;color:rgba(232,230,240,0.4);margin-bottom:3px">
                            <span>{name}</span>
                            <span>{val} / {maxval}</span>
                        </div>
                        <div class="comp-bar-wrap">
                            <div class="comp-bar-fill"
                                style="width:{pct}%;background:{color}"></div>
                        </div>
                    </div>""", unsafe_allow_html=True)

            # Threat status
            if result["threats"]:
                st.markdown(f"""<div class="threat-found">
                    ⚠ Threats detected: {', '.join(result['threats'])}
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div class="threat-clear">
                    ✓ Environment clear — no screen-sharing detected
                </div>""", unsafe_allow_html=True)

    with right:

        # Risk gauge
        st.markdown('<div class="section-label">Risk score</div>',
                    unsafe_allow_html=True)
        risk_val = result["risk_score"] if result else 0
        st.plotly_chart(
            build_gauge(risk_val),
            use_container_width=True,
            config={"displayModeBar": False}
        )

        # Decision box
        if result:
            dec = result["decision"]
            if dec == "APPROVED":
                st.markdown("""<div class="decision-approved">
                    <div class="decision-title" style="color:#4ECFA0">✓ Approved</div>
                    <div class="decision-sub">HMAC token verified by bank</div>
                </div>""", unsafe_allow_html=True)
            elif dec == "BLOCKED":
                st.markdown("""<div class="decision-blocked">
                    <div class="decision-title" style="color:#FF6B7A">✗ Blocked</div>
                    <div class="decision-sub">High risk — transaction rejected</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div class="decision-stepup">
                    <div class="decision-title" style="color:#FFB347">⚡ Step-up</div>
                    <div class="decision-sub">Additional verification required</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

        # System log
        st.markdown('<div class="section-label">System log</div>',
                    unsafe_allow_html=True)

        log_html = ""
        for line in reversed(st.session_state.log_lines[-10:]):
            css_class = {
                "success": "log-success",
                "warning": "log-warning",
                "error":   "log-error"
            }.get(line["level"], "")
            log_html += f"""<div class="log-line {css_class}">
                <span style="color:rgba(232,230,240,0.25)">{line['time']}</span>
                &nbsp;&nbsp;{line['msg']}
            </div>"""

        st.markdown(
            f'<div style="height:200px;overflow-y:auto">{log_html}</div>',
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # ── DEMO CONTROLS ──
    st.markdown('<div class="section-label">Demo controls — simulate transactions</div>',
                unsafe_allow_html=True)

    b1, b2, b3, _ = st.columns([1, 1, 1, 2])

    with b1:
        if st.button("✋ Human transaction", use_container_width=True):
            result = simulate_transaction("human")
            st.session_state.last_result = result
            st.session_state.transaction_count += 1
            st.session_state.approved_count    += 1
            st.session_state.risk_history.append(result["risk_score"])
            add_log("Transaction initiated", "info")
            add_log("200 sensor samples collected", "info")
            add_log(f"FFT computed — peak at ~10Hz", "info")
            add_log(f"Risk score: {result['risk_score']}/100", "info")
            add_log("Environment: CLEAR", "info")
            add_log(f"APPROVED — token generated ✓", "success")
            st.rerun()

    with b2:
        if st.button("💻 Replay attack", use_container_width=True):
            result = simulate_transaction("attack")
            st.session_state.last_result = result
            st.session_state.transaction_count += 1
            st.session_state.blocked_count     += 1
            st.session_state.risk_history.append(result["risk_score"])
            add_log("Transaction initiated", "info")
            add_log("Sensor data received", "info")
            add_log("FFT computed — 0Hz flat signal detected", "warning")
            add_log(f"Risk score: {result['risk_score']}/100", "warning")
            add_log("NO biological tremor — hardware idle", "error")
            add_log("BLOCKED — software replay detected ✗", "error")
            st.rerun()

    with b3:
        if st.button("📡 Screen-share threat", use_container_width=True):
            result = simulate_transaction("threat")
            st.session_state.last_result = result
            st.session_state.transaction_count += 1
            st.session_state.blocked_count     += 1
            st.session_state.risk_history.append(result["risk_score"])
            add_log("Transaction initiated", "info")
            add_log("200 sensor samples collected", "info")
            add_log("FFT computed — tremor detected", "info")
            add_log("THREAT: AnyDesk running — APP scam risk", "error")
            add_log(f"Risk score: {result['risk_score']}/100", "warning")
            add_log("BLOCKED — screen-share detected ✗", "error")
            st.rerun()


# ─────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────
render_dashboard()