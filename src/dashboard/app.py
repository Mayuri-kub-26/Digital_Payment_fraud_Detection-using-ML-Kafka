"""
FraudSense AI Dashboard — Digital Payment Fraud Detection
=========================================================
Fix log:
  • Replaced `for m in consumer` with consumer.poll() to fix
    "ValueError: generator already executing" on st.rerun()
  • auto_offset_reset='earliest' so we don't miss messages
  • Sidebar page navigation (Live Monitor / Manual Checker)
  • Bright, high-contrast professional fintech UI
"""
import streamlit as st
import json
import time
import os
import joblib
import pandas as pd
from kafka import KafkaConsumer

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FraudSense AI",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
BROKER      = os.getenv("KAFKA_BROKER", "localhost:9092")
TYPE_MAP    = {"PAYMENT": 0, "TRANSFER": 1, "CASH_OUT": 2, "DEBIT": 3, "CASH_IN": 4}
MODEL_PATH  = "src/model/fraud_model.pkl"

# ─── GLOBAL CSS ──────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

* { box-sizing: border-box; }

html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1e 0%, #0d1428 100%) !important;
    border-right: 1px solid rgba(0,200,255,0.15) !important;
}
[data-testid="stSidebar"] * { color: #e0e8ff !important; }
[data-testid="stSidebar"] .stRadio label {
    font-size: 1rem !important;
    font-weight: 600 !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    cursor: pointer !important;
}

/* ── Main bg ── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #060c1a 0%, #0b1530 50%, #060c1a 100%) !important;
}
[data-testid="stHeader"] { background: transparent !important; }

/* ── Hero ── */
.hero {
    display: flex; justify-content: space-between; align-items: center;
    padding: 24px 0 18px 0; margin-bottom: 4px;
    border-bottom: 1px solid rgba(0,200,255,0.18);
}
.hero-badge {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.18em;
    color: #00c8ff; background: rgba(0,200,255,0.1);
    border: 1px solid rgba(0,200,255,0.3);
    padding: 4px 12px; border-radius: 99px; display: inline-block; margin-bottom: 8px;
}
.hero-title {
    font-size: 2.6rem; font-weight: 900; margin: 0;
    background: linear-gradient(90deg, #00c8ff 0%, #a78bfa 60%, #ff3d71 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub { font-size: 1rem; color: #8ba4d4; font-weight: 500; margin-top: 4px; }
.live-chip {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(0,255,140,0.1); border: 1px solid rgba(0,255,140,0.3);
    border-radius: 99px; padding: 6px 16px; font-size: 0.82rem;
    font-weight: 700; color: #00ff8c; letter-spacing: 0.1em;
}
.live-dot {
    width: 8px; height: 8px; background: #00ff8c;
    border-radius: 50%; animation: pulse 1.4s infinite;
}
.offline-chip {
    background: rgba(255,61,113,0.1); border-color: rgba(255,61,113,0.3);
    color: #ff3d71;
}
.offline-dot { background: #ff3d71; animation: none; }
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50% { opacity:0.4; transform:scale(0.7); }
}
.refresh-ts { font-size: 0.75rem; color: #8aabcc; margin-top: 6px; text-align: right; }

/* ── KPI grid ── */
.kpi-grid {
    display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; margin: 20px 0;
}
.kpi-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 20px 22px; position: relative; overflow: hidden;
    transition: transform .2s, box-shadow .2s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
.kpi-icon { font-size: 1.6rem; margin-bottom: 8px; }
.kpi-val  { font-size: 2rem; font-weight: 800; line-height: 1; margin: 4px 0; }
.kpi-lbl  { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.1em; color: #a0bfe0; text-transform: uppercase; }
.kpi-bar  { height: 3px; border-radius: 99px; margin-top: 12px; background: rgba(255,255,255,0.06); }
.kpi-bar-fill { height: 100%; border-radius: 99px; }
.c-cyan  { color: #00c8ff; }
.c-red   { color: #ff3d71; }
.c-green { color: #00ff8c; }
.c-amber { color: #fbbf24; }
.b-cyan  { background: linear-gradient(90deg,#00c8ff,#0070ff); }
.b-red   { background: linear-gradient(90deg,#ff3d71,#ff0040); }
.b-green { background: linear-gradient(90deg,#00ff8c,#00b85a); }
.b-amber { background: linear-gradient(90deg,#fbbf24,#f59e0b); }
.kpi-accent-line {
    position: absolute; bottom: 0; left: 0; right: 0; height: 3px; border-radius: 0 0 16px 16px;
}

/* ── Risk gauge ── */
.gauge-wrap {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 16px 22px; display: flex; align-items: center;
    gap: 18px; margin: 0 0 20px 0;
}
.gauge-label { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.15em; color: #a0bfe0; }
.gauge-badge {
    font-size: 0.8rem; font-weight: 800; letter-spacing: 0.1em;
    border: 1.5px solid; border-radius: 99px; padding: 3px 12px;
    display: inline-block; margin-top: 3px;
}
.gauge-bar-bg {
    flex: 1; height: 10px; background: rgba(255,255,255,0.07);
    border-radius: 99px; overflow: hidden;
}
.gauge-bar-fill { height: 100%; border-radius: 99px; transition: width .5s ease; }
.gauge-pct { font-size: 1.1rem; font-weight: 800; min-width: 48px; text-align: right; }

/* ── Panels ── */
.panel-head {
    font-size: 0.78rem; font-weight: 800; letter-spacing: 0.15em;
    text-transform: uppercase; padding: 0 0 10px 0; margin-bottom: 4px;
    border-bottom: 2px solid;
    display: flex; align-items: center; gap: 8px;
}
.panel-count {
    font-size: 0.72rem; background: rgba(255,61,113,0.15);
    border: 1px solid rgba(255,61,113,0.3);
    color: #ff3d71; border-radius: 99px; padding: 2px 10px; margin-left: auto;
}

/* ── Scroll box ── */
.scroll-box {
    max-height: 420px; overflow-y: auto; padding-right: 4px;
    scrollbar-width: thin; scrollbar-color: rgba(0,200,255,0.2) transparent;
}
.scroll-box::-webkit-scrollbar { width: 4px; }
.scroll-box::-webkit-scrollbar-thumb { background: rgba(0,200,255,0.25); border-radius: 99px; }

/* ── Transaction row ── */
.tx-row {
    background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 12px 14px; margin-bottom: 8px;
    transition: background .15s;
}
.tx-row:hover { background: rgba(255,255,255,0.045); }
.tx-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.tx-left { display: flex; align-items: center; flex-wrap: wrap; gap: 5px; }
.type-pill {
    font-size: 0.65rem; font-weight: 800; letter-spacing: 0.1em;
    background: rgba(0,200,255,0.15); color: #00c8ff;
    border: 1px solid rgba(0,200,255,0.3); border-radius: 99px; padding: 2px 10px;
}
.type-pill-red {
    background: rgba(255,61,113,0.15); color: #ff3d71;
    border-color: rgba(255,61,113,0.3);
}
.tx-id    { font-size: 0.7rem; color: #7aaace; font-weight: 600; }
.tx-amt   { font-size: 1.05rem; font-weight: 800; color: #e2f0ff; }
.tx-amt-red { color: #ff3d71; }
.tx-meta  { font-size: 0.7rem; color: #90b8d8; margin: 3px 0 5px 0; }
.rtag {
    font-size: 0.6rem; font-weight: 700; border-radius: 99px;
    padding: 1px 7px; border: 1px solid;
}
.rtag-red   { background:rgba(255,61,113,0.12); color:#ff3d71; border-color:rgba(255,61,113,0.3); }
.rtag-amber { background:rgba(251,191,36,0.12); color:#fbbf24; border-color:rgba(251,191,36,0.3); }
.rtag-purple{ background:rgba(167,139,250,0.12);color:#a78bfa; border-color:rgba(167,139,250,0.3);}
.rtag-orange{ background:rgba(251,146,60,0.12); color:#fb923c; border-color:rgba(251,146,60,0.3); }

/* ── Score row ── */
.score-row  { display:flex; align-items:center; gap:8px; margin-top:6px; }
.score-lbl  { font-size:0.62rem; font-weight:700; letter-spacing:.08em; color:#90b8d8; min-width:80px; }
.score-bar-bg { flex:1; height:6px; background:rgba(255,255,255,0.07); border-radius:99px; overflow:hidden; }
.score-bar-fill { height:100%; border-radius:99px; transition:width .4s ease; }
.score-pct  { font-size:0.78rem; font-weight:800; min-width:34px; text-align:right; }

/* ── Alert row ── */
.al-row {
    background: rgba(255,61,113,0.05); border: 1px solid rgba(255,61,113,0.18);
    border-radius: 12px; padding: 12px 14px; margin-bottom: 8px;
}
.al-reason { font-size:0.68rem; color:#ff8fa8; margin-top:4px; }

/* ── Empty state ── */
.empty-state {
    text-align: center; padding: 40px 20px;
    color: #6a92b8; font-size: 0.9rem; font-weight: 500;
}

/* ── Divider ── */
.divider { height:1px; background:rgba(255,255,255,0.07); margin:24px 0; }

/* ── Manual checker ── */
.checker-header {
    font-size: 1.4rem; font-weight: 800; color: #e2f0ff; margin-bottom: 4px;
}
.checker-sub { font-size: 0.88rem; color: #90b8d8; margin-bottom: 24px; }
.result-card {
    border-radius: 16px; padding: 22px 26px; margin-top: 20px;
    animation: slideUp .35s ease;
}
.result-fraud       { background:rgba(255,61,113,0.10); border:2px solid #ff3d71; }
.result-suspicious  { background:rgba(255,140,0,0.08);  border:2px solid #ff8c00; }
.result-safe        { background:rgba(0,255,140,0.07);  border:2px solid #00ff8c; }
.result-title { font-size:1.7rem; font-weight:900; margin-bottom:6px; }
.result-sub   { font-size:0.92rem; color:#ccdff5; }
.result-reasons { margin-top:14px; font-size:0.82rem; color:#a8c4e4; line-height:1.6; }
.result-bar-wrap { margin:14px 0 6px 0; }
.result-bar-bg { height:12px; background:rgba(255,255,255,0.08); border-radius:99px; overflow:hidden; }
.result-bar-fill  { height:100%; border-radius:99px; transition:width .5s ease; }
.result-bar-labels { display:flex; justify-content:space-between; font-size:0.72rem; color:#7aaace; margin-top:4px; }
@keyframes slideUp { from{opacity:0;transform:translateY(12px);} to{opacity:1;transform:none;} }

/* ── Footer ── */
.footer {
    text-align:center; padding:20px; margin-top:32px;
    font-size:0.75rem; color:#7aaace;
    border-top:1px solid rgba(255,255,255,0.06);
}

/* ── Streamlit widgets pervasive dark-theme overrides ── */
[data-testid="stNumberInput"] div[data-baseweb="input"],
[data-testid="stTextInput"] div[data-baseweb="input"],
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="input"] {
    background-color: #0d1a30 !important;
    background: #0d1a30 !important;
    border-color: rgba(0,200,255,0.3) !important;
    color: #e8f4ff !important;
}

[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div[role="button"],
[data-testid="stSelectbox"] div[data-baseweb="select"] * {
    background-color: transparent !important;
    background: transparent !important;
    color: #e8f4ff !important;
    -webkit-text-fill-color: #e8f4ff !important;
}

/* Specific Transaction ID / UPI ID field styling */
[data-testid="stTextInput"] input {
    background: #0d1a30 !important;
    border: none !important;
}

/* Labels and section headers visibility */
[data-testid="stWidgetLabel"] p, label[data-testid="stWidgetLabel"] {
    color: #c8ddf5 !important;
    font-weight: 700 !important;
}

/* ── Checkboxes — full visible styling ── */
[data-testid="stCheckbox"] {
    padding: 4px 0 !important;
}
[data-testid="stCheckbox"] label {
    color: #d8ecff !important;
    font-size: 0.86rem !important;
    font-weight: 600 !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    cursor: pointer !important;
}
/* The custom checkbox box */
[data-testid="stCheckbox"] label span:first-child {
    width: 18px !important; height: 18px !important;
    border-radius: 5px !important;
    border: 2px solid rgba(0,200,255,0.55) !important;
    background: rgba(0,20,60,0.7) !important;
    flex-shrink: 0 !important;
    transition: all 0.15s ease !important;
}
/* Checked state — bright cyan fill */
[data-testid="stCheckbox"] input:checked + label span:first-child,
[data-testid="stCheckbox"] label:has(input:checked) span:first-child {
    background: linear-gradient(135deg, #0060cc, #00c8ff) !important;
    border-color: #00c8ff !important;
    box-shadow: 0 0 8px rgba(0,200,255,0.5) !important;
}
/* Hover highlight on row */
[data-testid="stCheckbox"] label:hover {
    color: #ffffff !important;
}
[data-testid="stCheckbox"] label:hover span:first-child {
    border-color: #00c8ff !important;
    box-shadow: 0 0 6px rgba(0,200,255,0.35) !important;
}
/* All text spans inside the label */
[data-testid="stCheckbox"] p,
[data-testid="stCheckbox"] label p,
[data-testid="stCheckbox"] span[data-testid="stCheckboxLabel"],
[data-testid="stCheckbox"] label span:not(:first-child) {
    color: #d8ecff !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
}

/* ── Form section headers (st.markdown "#### ...") ── */
.stMarkdown h4 { color: #a0c8f0 !important; font-size: 1rem !important; }

/* ── Analyze button ── */
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #0070ff 0%, #00c8ff 100%) !important;
    color: #fff !important; font-weight: 800 !important;
    border: none !important; border-radius: 10px !important;
    font-size: 1rem !important; letter-spacing: 0.05em !important;
    transition: opacity .2s !important;
}
div[data-testid="stButton"] button:hover { opacity: 0.85 !important; }
div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #0070ff 0%, #00c8ff 100%) !important;
    color: #fff !important; font-weight: 800 !important; font-size: 1.05rem !important;
    border: none !important; border-radius: 10px !important;
    transition: opacity .2s !important;
}
</style>
"""

# ─── LOAD MODEL (cached so it runs once) ─────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_model():
    try:
        bundle = joblib.load(MODEL_PATH)
        return bundle["model"], bundle["features"]
    except Exception as e:
        return None, None

clf, FEATURE_COLS = load_model()


# ─── KAFKA CONSUMERS (cached so connections persist) ─────────────────────────
@st.cache_resource(show_spinner=False)
def get_consumers():
    try:
        tx_consumer = KafkaConsumer(
            "transactions",
            bootstrap_servers=BROKER,
            auto_offset_reset="latest",
            value_deserializer=lambda x: json.loads(x.decode("utf-8", errors="ignore")),
            group_id="guardian_dash_tx_v1",
            enable_auto_commit=True,
            max_poll_records=50,
        )
        al_consumer = KafkaConsumer(
            "fraud_alerts",
            bootstrap_servers=BROKER,
            auto_offset_reset="latest",
            value_deserializer=lambda x: json.loads(x.decode("utf-8", errors="ignore")),
            group_id="guardian_dash_al_v1",
            enable_auto_commit=True,
            max_poll_records=50,
        )
        return tx_consumer, al_consumer, True
    except Exception:
        return None, None, False


def poll_kafka():
    """
    Safe Kafka polling using poll() — never iterates the consumer
    generator, so there's NO 'generator already executing' error.
    Returns (tx_msgs, alert_msgs, connected).
    """
    tx_consumer, al_consumer, connected = get_consumers()
    if not connected:
        return [], [], False
    try:
        tx_raw = tx_consumer.poll(timeout_ms=200, max_records=25)
        al_raw = al_consumer.poll(timeout_ms=200, max_records=25)
        tx_msgs = [m.value for plist in tx_raw.values() for m in plist]
        al_msgs = [m.value for plist in al_raw.values() for m in plist]
        return tx_msgs, al_msgs, True
    except Exception:
        return [], [], False


# ─── ML PREDICTION HELPER ────────────────────────────────────────────────────
def predict_txn(txn: dict):
    """Returns (is_fraud: int, probability: float) using XGBoost model."""
    if clf is None or FEATURE_COLS is None:
        return 0, 0.0
    amount       = float(txn.get("amount", 0))
    old_bal      = float(txn.get("oldbalanceOrg", 0))
    new_bal      = float(txn.get("newbalanceOrig", 0))
    tx_type      = txn.get("type", "PAYMENT")

    fd = {
        "type": TYPE_MAP.get(tx_type, 0),
        "amount": amount,
        "oldbalanceOrg": old_bal,
        "newbalanceOrig": new_bal,
        "balanceDiff": old_bal - new_bal,
        "highAmountFlag": 1 if amount > 30000 else 0,
        "round_amount_flag": txn.get("round_amount_flag", 0),
        "amount_just_below_threshold": txn.get("amount_just_below_threshold", 0),
        "account_age_days": txn.get("account_age_days", 500),
        "is_new_account": txn.get("is_new_account", 0),
        "avg_txn_amount": txn.get("avg_txn_amount", 5000),
        "txn_frequency_deviation": txn.get("txn_frequency_deviation", 1.0),
        "balance_utilization": txn.get("balance_utilization", 0.5),
        "is_new_device": txn.get("is_new_device", 0),
        "device_switch_count": txn.get("device_switch_count", 0),
        "is_emulator": txn.get("is_emulator", 0),
        "session_duration_anomaly": txn.get("session_duration_anomaly", 0),
        "multiple_sessions": txn.get("multiple_sessions", 0),
        "ip_country_mismatch": txn.get("ip_country_mismatch", 0),
        "vpn_detected": txn.get("vpn_detected", 0),
        "proxy_used": txn.get("proxy_used", 0),
        "location_change_rate": txn.get("location_change_rate", 0.1),
        "unusual_location": txn.get("unusual_location", 0),
        "is_international": txn.get("is_international", 0),
        "high_risk_country": txn.get("high_risk_country", 0),
        "hour": txn.get("hour", 12),
        "day_of_week": txn.get("day_of_week", 0),
        "unusual_hour_flag": txn.get("unusual_hour_flag", 0),
        "time_since_last_txn": txn.get("time_since_last_txn", 3600),
        "rapid_txn_flag": txn.get("rapid_txn_flag", 0),
        "otp_request_count": txn.get("otp_request_count", 1),
        "otp_bypass_attempt": txn.get("otp_bypass_attempt", 0),
        "failed_auth_count": txn.get("failed_auth_count", 0),
        "biometric_failed": txn.get("biometric_failed", 0),
        "security_question_failed": txn.get("security_question_failed", 0),
        "is_new_recipient": txn.get("is_new_recipient", 0),
        "recipient_blacklisted": txn.get("recipient_blacklisted", 0),
        "recipient_txn_count": txn.get("recipient_txn_count", 10),
        "same_recipient_rapid_txn": txn.get("same_recipient_rapid_txn", 0),
        "is_business_account": txn.get("is_business_account", 0),
        "high_risk_merchant": txn.get("high_risk_merchant", 0),
        "gift_card_request": txn.get("gift_card_request", 0),
        "wire_to_new_account": txn.get("wire_to_new_account", 0),
        "urgency_keywords_detected": txn.get("urgency_keywords_detected", 0),
        "shared_link_clicked": txn.get("shared_link_clicked", 0),
        "third_party_involved": txn.get("third_party_involved", 0),
        "phone_call_mentioned": txn.get("phone_call_mentioned", 0),
        "balance_to_amount_ratio": txn.get("balance_to_amount_ratio", 10.0),
        "amount_vs_avg_deviation": txn.get("amount_vs_avg_deviation", 0.5),
        "unusually_small_txn": txn.get("unusually_small_txn", 0),
        "consecutive_increasing_amounts": txn.get("consecutive_increasing_amounts", 0),
        "velocity_risk": txn.get("velocity_risk", 0),
        "overall_risk_score": txn.get("overall_risk_score", 0.1),
    }
    df   = pd.DataFrame([fd], columns=FEATURE_COLS)
    pred = int(clf.predict(df)[0])
    prob = float(clf.predict_proba(df)[0][1])
    return pred, prob


# ─── CONTEXTUAL FRAUD INTELLIGENCE AGENT ─────────────────────────────────────
# Detects real-world digital payment scam patterns based on how fraudsters
# actually operate. Each pattern adjusts the raw ML probability up or down
# and surfaces a human-readable explanation for the analyst / checker UI.
#
# Pattern reference (India UPI + global digital payments):
#   OTP Scam, SIM Swap, Phishing, Money Mule, Dormant Acct Activation,
#   Balance Drain, Gift Card Scam, Urgency/Social Engineering,
#   Lottery Scam, Structuring, Rapid Multi-Transfer, New Acct + High Value,
#   Business Legitimate Profile, Trusted Behavioral Pattern

CTX_PATTERN_META = {
    "OTP_SCAM":       ("#ff3d71", "OTP SCAM"),
    "SIM_SWAP":       ("#ff3d71", "SIM SWAP"),
    "PHISHING":       ("#ff3d71", "PHISHING"),
    "MONEY_MULE":     ("#ff3d71", "MONEY MULE"),
    "DORMANT_ACCT":   ("#ff5500", "DORMANT ACCT"),
    "BALANCE_DRAIN":  ("#ff5500", "BALANCE DRAIN"),
    "GIFT_CARD_SCAM": ("#ff8c00", "GIFT CARD SCAM"),
    "URGENCY_SCAM":   ("#ff8c00", "URGENCY / SOC-ENG"),
    "LOTTERY_SCAM":   ("#ff8c00", "LOTTERY SCAM"),
    "STRUCTURING":    ("#ff8c00", "STRUCTURING"),
    "RAPID_MULTI":    ("#ff8c00", "RAPID MULTI-TXN"),
    "NEW_ACCT_HV":    ("#ff8c00", "NEW ACCT + HIGH VAL"),
    "BUSINESS_LEGIT": ("#00ff8c", "BUSINESS PROFILE"),
    "TRUSTED_PATTERN":("#00ff8c", "TRUSTED PATTERN"),
}


def contextual_analysis(txn: dict, raw_prob: float) -> dict:
    """
    Situational AI layer applied on top of the raw XGBoost probability.
    Produces an adjusted_prob, a list of detected pattern keys, and
    human-readable reasons for each pattern.
    """
    amount         = float(txn.get("amount", 0))
    old_bal        = float(txn.get("oldbalanceOrg", 0))
    new_bal        = float(txn.get("newbalanceOrig", 0))
    acct_age       = int(txn.get("account_age_days", 365))
    is_business    = int(txn.get("is_business_account", 0))
    rcpt_count     = int(txn.get("recipient_txn_count", 10))
    is_new_rcpt    = int(txn.get("is_new_recipient", 0))
    vpn            = int(txn.get("vpn_detected", 0))
    proxy          = int(txn.get("proxy_used", 0))
    otp_bypass     = int(txn.get("otp_bypass_attempt", 0))
    biometric_fail = int(txn.get("biometric_failed", 0))
    failed_auth    = int(txn.get("failed_auth_count", 0))
    blacklisted    = int(txn.get("recipient_blacklisted", 0))
    just_below     = int(txn.get("amount_just_below_threshold", 0))
    gift_card      = int(txn.get("gift_card_request", 0))
    urgency        = int(txn.get("urgency_keywords_detected", 0))
    phishing_link  = int(txn.get("shared_link_clicked", 0))
    rapid_txn      = int(txn.get("rapid_txn_flag", 0))
    same_rcpt_rapid= int(txn.get("same_recipient_rapid_txn", 0))
    new_acct       = int(txn.get("is_new_account", 0))
    high_amt_flag  = int(txn.get("highAmountFlag", 0))
    upi_risk       = float(txn.get("upi_risk_score", 0.0))

    patterns = []
    reasons  = []
    modifier = 0.0

    # ── 1. OTP SCAM ──────────────────────────────────────────────────────────
    # Fraudster calls pretending to be bank/app support, tricks victim into
    # sharing OTP, then initiates a transfer to a new/unverified recipient.
    if otp_bypass and (is_new_rcpt or rapid_txn):
        modifier += 0.30
        patterns.append("OTP_SCAM")
        reasons.append(
            "🔴 [OTP SCAM] OTP bypass detected with a new/rapid transfer. "
            "Scammers impersonate bank support to extract OTPs from victims — "
            "this is India's #1 digital fraud vector."
        )

    # ── 2. SIM SWAP ATTACK ───────────────────────────────────────────────────
    # Criminal ports victim's phone number to a new SIM → intercepts OTPs →
    # logs into banking app. Signals: biometric failures + multiple auth fails + VPN.
    if vpn and biometric_fail and failed_auth > 1:
        modifier += 0.28
        patterns.append("SIM_SWAP")
        reasons.append(
            "🔴 [SIM SWAP] VPN + biometric failure + multiple auth failures — "
            "classic SIM swap fingerprint. A cloned SIM intercepts OTPs, "
            "allowing the attacker to authenticate as the real account owner."
        )

    # ── 3. PHISHING / CREDENTIAL THEFT ───────────────────────────────────────
    # Victim clicks a fake link (fake bank site, UPI QR) → credentials stolen →
    # fraudster initiates transfer. Phishing + new recipient = high confidence.
    if phishing_link and (otp_bypass or is_new_rcpt or vpn):
        modifier += 0.25
        patterns.append("PHISHING")
        reasons.append(
            "🔴 [PHISHING] A phishing/shared link was clicked before this transaction. "
            "Session tokens or credentials may have been harvested. "
            "Fake UPI QR codes, fake bank login pages are common attack vectors."
        )

    # ── 4. MONEY MULE + DORMANT ACCOUNT ACTIVATION ───────────────────────────
    # Criminal uses a victim's dormant account to receive stolen funds, then
    # immediately forward them. Pattern: near-zero balance → large credit → all gone.
    dormant_then_drain = (
        old_bal <= 500 and
        amount > 1500 and
        (new_bal < 300 or (old_bal >= 0 and new_bal < old_bal * 0.10))
    )
    if dormant_then_drain:
        modifier += 0.38
        patterns.append("DORMANT_ACCT")
        patterns.append("MONEY_MULE")
        reasons.append(
            f"🔴 [DORMANT ACTIVATION / MONEY MULE] Account had near-zero balance "
            f"(₹{old_bal:.0f}), received ₹{amount:,.0f}, and balance is now ≈₹{new_bal:.0f}. "
            "Fraudsters recruit innocent people ('mules') or hack dormant accounts to "
            "layer stolen funds — the #1 money laundering technique in digital payments."
        )
    elif old_bal > 500 and new_bal < old_bal * 0.05 and amount > 5000:
        # ── 5. BALANCE DRAIN (account takeover sweep) ─────────────────────
        modifier += 0.22
        patterns.append("BALANCE_DRAIN")
        reasons.append(
            f"🔴 [BALANCE DRAIN] Account balance ₹{old_bal:,.0f} nearly fully drained "
            f"in a single transaction. Account takeover attackers sweep all funds "
            "immediately before the victim notices or the bank can intervene."
        )

    # ── 6. GIFT CARD SCAM ────────────────────────────────────────────────────
    # Scammers request payment via Amazon/Google Play gift cards (untraceable).
    # Used in tech-support scams, grandparent scams, fake tax demands.
    if gift_card:
        modifier += 0.28
        patterns.append("GIFT_CARD_SCAM")
        reasons.append(
            "🟠 [GIFT CARD SCAM] Gift card payment requested. No legitimate bank, "
            "government, or business ever demands payment via gift cards. "
            "This is a confirmed social engineering tactic."
        )

    # ── 7. URGENCY / SOCIAL ENGINEERING ─────────────────────────────────────
    # 'Emergency! Your account will be blocked!' — urgency bypasses rational thinking.
    # Used in: emergency scams, fake customs/police calls, account-suspension threats.
    if urgency and (is_new_rcpt or high_amt_flag):
        modifier += 0.20
        if "PHISHING" not in patterns:
            patterns.append("URGENCY_SCAM")
            reasons.append(
                "🟠 [URGENCY / SOCIAL ENGINEERING] Urgency language detected + new recipient "
                "or high amount. Scammers create artificial panic: "
                "'Your account will be suspended!', 'Pay now or face arrest!', "
                "'Your relative is in the hospital!' — all are social engineering scripts."
            )

    # ── 8. LOTTERY / PRIZE SCAM ──────────────────────────────────────────────
    # 'You won ₹50 lakh! Pay ₹500 processing fee.'
    # Signal: high-risk UPI handle (suspicious keywords) + urgency combined.
    if upi_risk > 0.35 and urgency and "URGENCY_SCAM" not in patterns:
        modifier += 0.20
        patterns.append("LOTTERY_SCAM")
        reasons.append(
            "🟠 [LOTTERY / PRIZE SCAM] Suspicious UPI handle combined with urgency signals. "
            "Lottery scams promise large winnings but demand a small 'processing fee' first. "
            "Victims lose the fee and receive nothing."
        )

    # ── 9. STRUCTURING (Smurfing) ─────────────────────────────────────────────
    # Breaking large amounts into chunks just below ₹5k/10k/25k/50k reporting limits.
    # Known as 'smurfing' — a classic anti-detection technique for money laundering.
    if just_below:
        modifier += 0.16
        patterns.append("STRUCTURING")
        reasons.append(
            "🟠 [STRUCTURING / SMURFING] Amount is structured just below a common "
            "reporting threshold (₹4,999 / ₹9,999 / ₹24,999 / ₹49,999). "
            "Fraudsters deliberately split or size amounts to fly under automated alert systems."
        )

    # ── 10. RAPID MULTI-TRANSFER (Layering) ──────────────────────────────────
    # Multiple fast transfers to same/different recipients — layering stolen money.
    if rapid_txn and same_rcpt_rapid and "OTP_SCAM" not in patterns:
        modifier += 0.18
        patterns.append("RAPID_MULTI")
        reasons.append(
            "🟠 [RAPID MULTI-TRANSFER / LAYERING] Multiple rapid consecutive transfers "
            "to the same recipient detected. Fraudsters move funds quickly in chains "
            "to make tracing harder before a bank freeze can be applied."
        )

    # ── 11. NEW ACCOUNT + HIGH VALUE ─────────────────────────────────────────
    # Fresh accounts created specifically for one or two large theft transfers.
    if new_acct and amount > 10000 and not is_business and "DORMANT_ACCT" not in patterns:
        modifier += 0.14
        patterns.append("NEW_ACCT_HV")
        reasons.append(
            f"🟠 [NEW ACCOUNT + HIGH VALUE] A very new account initiating ₹{amount:,.0f} transfer. "
            "Fraudsters routinely open fresh accounts under fake KYC or stolen identities "
            "to perform a single large theft and then abandon the account."
        )

    # ── 12. BUSINESS PROFILE — LEGITIMATE HIGH-VALUE ─────────────────────────
    # Established businesses legitimately make large payments regularly.
    # If the environment is clean (no VPN/OTP/phishing), reduce risk.
    clean_env = not vpn and not proxy and not otp_bypass and not phishing_link
    if is_business and acct_age > 180 and clean_env:
        if high_amt_flag and rcpt_count > 3:
            modifier -= 0.22
            patterns.append("BUSINESS_LEGIT")
            reasons.append(
                f"✅ [BUSINESS PROFILE] Established business account ({acct_age}d old) "
                f"with a known recipient ({rcpt_count}+ prior transactions) in a clean "
                "network environment. High-value transfers are expected — risk significantly reduced."
            )
        elif high_amt_flag:
            modifier -= 0.10
            patterns.append("BUSINESS_LEGIT")
            reasons.append(
                "✅ [BUSINESS PROFILE] Business account with good standing. "
                "Recipient is relatively new but account history and environment are clean."
            )

    # ── 13. TRUSTED BEHAVIORAL PATTERN ───────────────────────────────────────
    # Long-standing account + frequently-used recipient + clean network = genuine signal.
    if (acct_age > 365 and rcpt_count > 10 and not is_new_rcpt
            and not blacklisted and not vpn and not urgency
            and "BUSINESS_LEGIT" not in patterns):
        modifier -= 0.10
        patterns.append("TRUSTED_PATTERN")
        reasons.append(
            f"✅ [TRUSTED PATTERN] Long-standing account ({acct_age}d) with a "
            f"frequently-used recipient ({rcpt_count} prior transactions) and a clean "
            "digital environment. This profile is consistent with genuine payment behavior."
        )

    adjusted = round(min(1.0, max(0.0, raw_prob + modifier)), 3)
    return {
        "adjusted_prob": adjusted,
        "raw_prob":      round(raw_prob, 3),
        "patterns":      patterns,
        "reasons":       reasons,
        "modifier":      round(modifier, 3),
    }


# ─── COLOUR HELPERS ──────────────────────────────────────────────────────────
def score_color(pct: int) -> str:
    """Red only for >= 80% (confirmed fraud); orange for 40-79%; green below 40%."""
    if pct >= 80: return "#ff3d71"   # red  — HIGH FRAUD (80%+)
    if pct >= 40: return "#ff8c00"   # orange — SUSPICIOUS (40-79%)
    return "#00ff8c"                  # green — LOW RISK (<40%)


# ─── PAGE: LIVE MONITOR ──────────────────────────────────────────────────────
def page_live():
    # Init session state
    for k, v in [
        ("tx_feed", []), ("al_feed", []), ("seen_tx", set()),
        ("seen_al", set()), ("total", 0), ("fraud_cnt", 0),
        ("volume", 0.0), ("tx_scores", {}), ("tx_patterns", {}),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    # Poll Kafka (safe — uses poll(), no generator iteration)
    tx_msgs, al_msgs, kafka_ok = poll_kafka()

    for v in tx_msgs:
        tid = v.get("transactionId", "")
        if tid and tid not in st.session_state.seen_tx:
            st.session_state.seen_tx.add(tid)
            st.session_state.tx_feed.append(v)
            st.session_state.total  += 1
            st.session_state.volume += float(v.get("amount", 0))
            _, prob = predict_txn(v)
            ctx  = contextual_analysis(v, prob)
            st.session_state.tx_scores[tid]  = ctx["adjusted_prob"]
            st.session_state.tx_patterns[tid] = ctx["patterns"]

    for v in al_msgs:
        tid = v.get("transactionId", "")
        if tid and tid not in st.session_state.seen_al:
            st.session_state.seen_al.add(tid)
            st.session_state.al_feed.append(v)
            st.session_state.fraud_cnt += 1

    st.session_state.tx_feed = st.session_state.tx_feed[-300:]
    st.session_state.al_feed = st.session_state.al_feed[-150:]

    total     = st.session_state.total
    fraud_cnt = st.session_state.fraud_cnt
    volume    = st.session_state.volume
    safety    = max(0.0, 100.0 - fraud_cnt / max(total, 1) * 100)
    fraud_pct = min(100.0, fraud_cnt / max(total, 1) * 100)

    # ── Header ──
    live_html = (
        '<div class="live-chip"><div class="live-dot"></div>LIVE</div>'
        if kafka_ok else
        '<div class="live-chip offline-chip"><div class="live-dot offline-dot"></div>KAFKA OFFLINE</div>'
    )
    st.markdown(f"""
    <div class="hero">
        <div>
            <div class="hero-badge">🛡️ AI SECURITY &nbsp;·&nbsp; REAL-TIME MONITORING</div>
            <div class="hero-title">FraudSense AI</div>
            <div class="hero-sub">Digital Payment Fraud Detection Platform</div>
        </div>
        <div style="text-align:right;">
            {live_html}
            <div class="refresh-ts">Refreshed: {time.strftime('%H:%M:%S')}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── KPI Cards ──
    safety_w = f"{safety:.1f}%"
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon">📥</div>
            <div class="kpi-val c-cyan">{total:,}</div>
            <div class="kpi-lbl">Transactions Processed</div>
            <div class="kpi-bar"><div class="kpi-bar-fill b-cyan" style="width:100%"></div></div>
            <div class="kpi-accent-line b-cyan"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🚨</div>
            <div class="kpi-val c-red">{fraud_cnt:,}</div>
            <div class="kpi-lbl">Fraud Alerts Blocked</div>
            <div class="kpi-bar"><div class="kpi-bar-fill b-red" style="width:{min(100,fraud_pct*5):.1f}%"></div></div>
            <div class="kpi-accent-line b-red"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🛡️</div>
            <div class="kpi-val c-green">{safety:.1f}%</div>
            <div class="kpi-lbl">System Safety Score</div>
            <div class="kpi-bar"><div class="kpi-bar-fill b-green" style="width:{safety:.1f}%"></div></div>
            <div class="kpi-accent-line b-green"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">💰</div>
            <div class="kpi-val c-amber">${volume/1000:,.1f}K</div>
            <div class="kpi-lbl">Volume Monitored</div>
            <div class="kpi-bar"><div class="kpi-bar-fill b-amber" style="width:100%"></div></div>
            <div class="kpi-accent-line b-amber"></div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── System Risk Gauge ──
    rlabel = "LOW RISK" if fraud_pct < 5 else ("MEDIUM RISK" if fraud_pct < 15 else "HIGH RISK")
    rcol   = "#00ff8c" if fraud_pct < 5 else ("#fbbf24" if fraud_pct < 15 else "#ff3d71")
    st.markdown(f"""
    <div class="gauge-wrap">
        <div>
            <div class="gauge-label">SYSTEM RISK LEVEL</div>
            <div class="gauge-badge" style="color:{rcol};border-color:{rcol}50;">{rlabel}</div>
        </div>
        <div class="gauge-bar-bg">
            <div class="gauge-bar-fill" style="width:{fraud_pct:.2f}%;background:{rcol};box-shadow:0 0 10px {rcol}60;"></div>
        </div>
        <div class="gauge-pct" style="color:{rcol};">{fraud_pct:.1f}%</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Dual Panel ──
    col1, col2 = st.columns(2, gap="large")

    # LEFT — Payment Stream
    with col1:
        hcol, fcol = st.columns([3, 1])
        with hcol:
            st.markdown("""
            <div class="panel-head" style="color:#00c8ff;border-color:#00c8ff30;">
                ⟳ &nbsp;PAYMENT STREAM
            </div>""", unsafe_allow_html=True)
        with fcol:
            tx_filter = st.selectbox(
                "type",
                ["ALL", "CASH_OUT", "TRANSFER", "PAYMENT", "CASH_IN", "DEBIT"],
                label_visibility="collapsed", key="tx_filter"
            )

        feed = list(reversed(st.session_state.tx_feed))
        if tx_filter != "ALL":
            feed = [x for x in feed if x.get("type") == tx_filter]

        if not feed:
            html = '<div class="empty-state">📡 Waiting for transactions…</div>'
        else:
            html = ""
            for t in feed[:60]:
                amt     = float(t.get("amount", 0))
                ttype   = t.get("type", "TXN")
                tid     = t.get("transactionId", "—")
                ts_raw  = t.get("timestamp", "")
                ts_str  = ts_raw[11:19] if len(ts_raw) >= 19 else "—"
                sender  = t.get("nameOrig", "—")[:18]
                recv    = t.get("nameDest", "—")[:18]
                hour    = t.get("hour", 12)
                age     = t.get("account_age_days", "?")

                # ML score + contextual analysis
                adj_prob = st.session_state.tx_scores.get(tid, None)
                ctx_pats = st.session_state.tx_patterns.get(tid, None)
                if adj_prob is None:
                    _, raw_p  = predict_txn(t)
                    ctx_       = contextual_analysis(t, raw_p)
                    adj_prob   = ctx_["adjusted_prob"]
                    ctx_pats   = ctx_["patterns"]
                    st.session_state.tx_scores[tid]  = adj_prob
                    st.session_state.tx_patterns[tid] = ctx_pats
                sc_pct  = int(adj_prob * 100)
                sc_col  = score_color(sc_pct)

                # Signal tags (raw flags)
                tags = ""
                if t.get("is_new_account"):      tags += '<span class="rtag rtag-red">NEW-ACCT</span> '
                if t.get("is_new_device"):        tags += '<span class="rtag rtag-amber">NEW-DEV</span> '
                if t.get("vpn_detected"):         tags += '<span class="rtag rtag-red">VPN</span> '
                if t.get("unusual_hour_flag"):    tags += '<span class="rtag rtag-amber">ODD-HOUR</span> '
                if t.get("otp_bypass_attempt"):   tags += '<span class="rtag rtag-red">OTP-BYPASS</span> '
                if t.get("is_new_recipient"):     tags += '<span class="rtag rtag-purple">NEW-RCPT</span> '
                if t.get("gift_card_request"):    tags += '<span class="rtag rtag-red">GIFT-SCAM</span> '
                if t.get("biometric_failed"):     tags += '<span class="rtag rtag-red">BIO-FAIL</span> '
                if t.get("urgency_keywords_detected"): tags += '<span class="rtag rtag-orange">URGENT</span> '
                if t.get("shared_link_clicked"):  tags += '<span class="rtag rtag-red">PHISHING</span> '

                # Contextual AI pattern badges
                ctx_tags = ""
                for pat in (ctx_pats or []):
                    meta = CTX_PATTERN_META.get(pat)
                    if meta:
                        col, label = meta
                        ctx_tags += (f'<span style="font-size:0.52rem;font-weight:800;'
                                     f'padding:2px 6px;border-radius:3px;margin-left:3px;'
                                     f'background:{col}22;color:{col};border:1px solid {col}55;'
                                     f'font-family:JetBrains Mono,monospace;letter-spacing:0.5px;'
                                     f'white-space:nowrap;">🔍 {label}</span>')

                verdict_line = (
                    f'<div style="font-size:0.58rem;color:{sc_col};font-weight:700;'
                    f'font-family:JetBrains Mono,monospace;margin-top:3px;letter-spacing:0.5px;">'
                    f'⬡ CTX-AI VERDICT: {"CONFIRMED FRAUD" if sc_pct>=80 else ("SUSPICIOUS" if sc_pct>=40 else "GENUINE")}</div>'
                ) if ctx_pats else ""

                html += f"""
<div class="tx-row">
<div class="tx-top">
<div class="tx-left">
<span class="type-pill">{ttype}</span>
<span class="tx-id">#{tid[-8:]}</span>
{tags}
</div>
<div class="tx-amt">${amt:,.0f}</div>
</div>
<div style="margin-bottom:4px;">{ctx_tags}</div>
<div class="tx-meta">{sender} &rarr; {recv} &nbsp;|&nbsp; {ts_str} &nbsp;|&nbsp; Acct {age}d &nbsp;|&nbsp; {hour:02d}:00h</div>
<div class="score-row">
<span class="score-lbl">AI FRAUD RISK</span>
<div class="score-bar-bg">
<div class="score-bar-fill" style="width:{sc_pct}%;background:{sc_col};box-shadow:0 0 6px {sc_col}60;"></div>
</div>
<span class="score-pct" style="color:{sc_col};">{sc_pct}%</span>
</div>
{verdict_line}
</div>
"""

        st.markdown(f'<div class="scroll-box">{html}</div>', unsafe_allow_html=True)

    # RIGHT — Fraud Alerts
    with col2:
        st.markdown(f"""
<div class="panel-head" style="color:#ff3d71;border-color:#ff3d7130;">
⚠ &nbsp;THREAT INTELLIGENCE
<span class="panel-count">{fraud_cnt} alerts</span>
</div>""", unsafe_allow_html=True)

        alerts = list(reversed(st.session_state.al_feed))
        if not alerts:
            al_html = '<div class="empty-state">🛡️ All Clear — No threats detected</div>'
        else:
            al_html = ""
            for a in alerts[:60]:
                o      = a.get("original_txn", {})
                sc     = a.get("score", 0.95)
                amt    = float(o.get("amount", 0))
                ttype  = o.get("type", "FRAUD")
                tid    = o.get("transactionId", "—")[-8:]
                ts_raw = o.get("timestamp", "")
                ts_str = ts_raw[11:19] if len(ts_raw) >= 19 else "—"
                sender = o.get("nameOrig", "—")[:18]
                recv   = o.get("nameDest", "—")[:18]
                reason = a.get("reason", "")[:80]
                sc_pct = int(sc * 100)
                sc_col = score_color(sc_pct)

                al_html += f"""
<div class="al-row">
<div class="tx-top">
<div class="tx-left">
<span class="type-pill type-pill-red">⚠ {ttype}</span>
<span class="tx-id" style="color:#ff6b88;">#{tid}</span>
</div>
<div class="tx-amt tx-amt-red">${amt:,.0f}</div>
</div>
<div class="tx-meta">{sender} &rarr; {recv} &nbsp;|&nbsp; {ts_str}</div>
<div class="score-row">
<span class="score-lbl">AI FRAUD SCORE</span>
<div class="score-bar-bg">
<div class="score-bar-fill" style="width:{sc_pct}%;background:{sc_col};box-shadow:0 0 8px {sc_col}70;"></div>
</div>
<span class="score-pct" style="color:{sc_col};">{sc_pct}%</span>
</div>
<div class="al-reason">{reason}</div>
</div>
"""

        st.markdown(f'<div class="scroll-box">{al_html}</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="footer">Securing Digital Payments with Intelligent Fraud Detection
    &nbsp;·&nbsp; © 2026 &nbsp;·&nbsp; {time.strftime('%Y-%m-%d')}</div>""",
    unsafe_allow_html=True)

    # Auto-refresh every ~2s
    time.sleep(2)
    st.rerun()


# ─── UPI ID ANALYSER ─────────────────────────────────────────────────────────
import re as _re

# Known legitimate bank VPA suffixes
LEGIT_BANKS = {
    "okaxis","okhdfcbank","okicici","oksbi","paytm","ybl","ibl","axl",
    "upi","apl","barodampay","centralbank","cub","dbs","federal","hsbc",
    "icici","kotak","rbl","sbi","scb","unionbank","utbi","vijb","hdfcbank",
    "indus","pnb","idfcbank","idbi","aubank","jsb","kbl","lvb","mahb",
    "nsdl","obc","psb","scbl","uboi","uco","allbank","andb","boi","bob",
    "corporation","dena","indian","mahagram","postbank","saraswat","tjsb",
    "abfspay","airtel","amazon","gpay","phonepe","slice","cred",
}

SUSPICIOUS_KEYWORDS = {
    "win","prize","lottery","bonus","lucky","gift","free","reward","earn",
    "cashback","offer","promo","urgent","help","crisis","loan","agent",
    "refund","tax","gov","govt","police","cbi","irs","income","fund",
    "customer","care","support","service","bank","verify","kyc","alert",
    "update","rbi","tds","fraud","victim","block","suspend","debit",
}

def analyse_upi(upi_id: str) -> dict:
    """
    Parses a UPI VPA (handle@bank) and returns a dict with:
      - is_valid: bool
      - handle / bank_vpa
      - risk_flags: list[str]  — human-readable warnings
      - upi_risk_score: 0-1 float
      - auto_signals: dict of feature overrides for the ML txn dict
    """
    upi_id = upi_id.strip().lower()
    result = {
        "is_valid": False,
        "handle": "",
        "bank_vpa": "",
        "risk_flags": [],
        "upi_risk_score": 0.0,
        "auto_signals": {},
    }

    if not upi_id:
        return result

    # Basic format check: must contain exactly one '@'
    if upi_id.count("@") != 1:
        result["risk_flags"].append("Invalid UPI format (must be handle@bank)")
        result["upi_risk_score"] = 0.6
        return result

    handle, bank = upi_id.split("@", 1)
    result["handle"]   = handle
    result["bank_vpa"] = bank
    result["is_valid"] = True

    flags  = []
    score  = 0.0
    auto   = {}

    # ── 1. Numeric-only handle (e.g. 9876543210@paytm) — can be legit but also used in scams
    if _re.fullmatch(r"\d+", handle):
        if len(handle) == 10:
            pass  # Common phone-based UPI, neutral
        else:
            flags.append("Numeric-only handle with unusual length — potential throwaway account")
            score += 0.15
            auto["is_new_account"] = 1

    # ── 2. Very short handle
    if len(handle) < 4:
        flags.append(f"Suspiciously short UPI handle ({handle!r})")
        score += 0.2
        auto["is_new_account"] = 1

    # ── 3. Random-looking handle (lots of digits mixed with letters)
    digit_ratio = sum(c.isdigit() for c in handle) / max(len(handle), 1)
    if digit_ratio > 0.6 and not _re.fullmatch(r"\d+", handle):
        flags.append("High digit-to-letter ratio — looks like a randomly generated ID")
        score += 0.2

    # ── 4. Suspicious keywords in handle
    handle_words = _re.split(r"[^a-z]+", handle)
    matched_kw = SUSPICIOUS_KEYWORDS.intersection(handle_words)
    if matched_kw:
        flags.append(f"Handle contains suspicious keyword(s): {', '.join(sorted(matched_kw))}")
        score += 0.35
        auto["urgency_keywords_detected"] = 1
        auto["recipient_blacklisted"] = 1

    # ── 5. Unknown / non-standard bank VPA
    if bank not in LEGIT_BANKS:
        flags.append(f"Unknown bank VPA suffix '@{bank}' — not a recognised payment provider")
        score += 0.25
        auto["is_new_recipient"] = 1

    # ── 6. 'test', 'demo', 'temp' handles
    if any(w in handle for w in ["test","demo","temp","fake","dummy","null"]):
        flags.append("Handle looks like a test/fake account")
        score += 0.4
        auto["recipient_blacklisted"] = 1

    result["risk_flags"]      = flags
    result["upi_risk_score"]  = min(1.0, round(score, 2))
    result["auto_signals"]    = auto
    return result


# ─── PAGE: MANUAL FRAUD CHECKER ──────────────────────────────────────────────
def page_checker():
    st.markdown("""
    <div style="margin-bottom:8px;">
        <div class="hero-badge">🔍 FRAUD PREDICTION ENGINE</div>
        <div class="hero-title" style="font-size:2rem;margin:6px 0 2px 0;">Manual Payment Checker</div>
        <div class="hero-sub">Enter a UPI ID + payment details to instantly predict fraud using the XGBoost AI model.</div>
    </div>
    <div class="divider"></div>""", unsafe_allow_html=True)

    if clf is None:
        st.error("⚠️ Model not loaded. Make sure `src/model/fraud_model.pkl` exists.")
        return

    # ── Extra CSS for UPI card ──
    st.markdown("""
    <style>
    .upi-card {
        background: linear-gradient(135deg, rgba(0,200,255,0.07) 0%, rgba(0,40,80,0.15) 100%);
        border: 1.5px solid rgba(0,200,255,0.3);
        border-radius: 14px; padding: 20px 24px 16px 24px; margin-bottom: 20px;
    }
    .upi-title { font-size:0.75rem; font-weight:800; letter-spacing:.14em; color:#00c8ff; margin-bottom:8px; }
    .upi-tag {
        display:inline-block; font-size:0.68rem; font-weight:700;
        border-radius:99px; padding:3px 10px; border:1px solid; margin:2px 3px 2px 0;
    }
    .upi-tag-ok   { background:rgba(0,255,140,0.1); color:#00ff8c; border-color:rgba(0,255,140,0.3); }
    .upi-tag-warn { background:rgba(251,191,36,0.1); color:#fbbf24; border-color:rgba(251,191,36,0.3); }
    .upi-tag-bad  { background:rgba(255,61,113,0.1); color:#ff3d71; border-color:rgba(255,61,113,0.3); }
    </style>
    """, unsafe_allow_html=True)

    # ── UPI ID field (outside form so it can live-preview) ──
    st.markdown('<div class="upi-title">📲 RECIPIENT UPI ID</div>', unsafe_allow_html=True)
    upi_input = st.text_input(
        "Recipient UPI ID",
        placeholder="e.g. rahul@okaxis  or  9876543210@paytm",
        label_visibility="collapsed",
        key="upi_field",
    )

    upi_info = analyse_upi(upi_input)

    # Live UPI preview
    if upi_input:
        if not upi_info["is_valid"]:
            upi_html = '<span class="upi-tag upi-tag-bad">⚠ Invalid UPI format</span>'
        else:
            upi_html = f'<span class="upi-tag upi-tag-ok">✓ {upi_info["handle"]}@{upi_info["bank_vpa"]}</span>'
            for flag in upi_info["risk_flags"]:
                upi_html += f'<span class="upi-tag upi-tag-bad">⚠ {flag[:60]}</span>'
            if not upi_info["risk_flags"]:
                upi_html += '<span class="upi-tag upi-tag-ok">✓ No UPI risk signals detected</span>'
        st.markdown(f'<div class="upi-card">{upi_html}</div>', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Main form ──
    with st.form("checker_form", clear_on_submit=False):
        st.markdown("#### 💳 &nbsp;Transaction Details")
        c1, c2, c3, c4 = st.columns(4)
        with c1: m_type   = st.selectbox("Transaction Type", ["PAYMENT","TRANSFER","CASH_OUT","DEBIT","CASH_IN"])
        with c2: m_amount = st.number_input("Amount (₹)", min_value=1.0, max_value=10_000_000.0, value=5000.0, step=100.0)
        with c3: m_obal   = st.number_input("Balance Before (₹)", min_value=0.0, value=50000.0, step=1000.0)
        with c4: m_nbal   = st.number_input("Balance After (₹)", min_value=0.0, value=45000.0, step=1000.0)

        st.markdown("---")
        st.markdown("#### 📋 &nbsp;Account & Timing")
        c5, c6 = st.columns(2)
        with c5:
            m_hour     = st.slider("Transaction Hour (0–23)", 0, 23, 14)
            m_acct_age = st.number_input("Account Age (days)", min_value=0, max_value=5000, value=365)
        with c6:
            m_new_dev  = st.checkbox("🖥️  New / Unknown Device")
            m_vpn      = st.checkbox("🔒  VPN / Proxy Detected")
            m_new_rcpt = st.checkbox("🧾  New Recipient (manual override)")
            m_urgent   = st.checkbox("⚡  Urgency Keywords in Message")

        st.markdown("---")
        st.markdown("#### 🚩 &nbsp;Additional Risk Signals")
        c7, c8, c9 = st.columns(3)
        with c7:
            m_otp      = st.checkbox("🔑  OTP Bypass Attempt")
            m_bio      = st.checkbox("🖐️  Biometric Auth Failed")
            m_business = st.checkbox("💼  Business / Merchant Account")
        with c8:
            m_gift  = st.checkbox("🎁  Gift Card Request")
            m_black = st.checkbox("⛔  Recipient Blacklisted (manual override)")
        with c9:
            m_link = st.checkbox("🎣  Phishing Link Clicked")
            m_emul = st.checkbox("📱  Emulator Detected")

        submitted = st.form_submit_button("🔍  Analyze Transaction Now", use_container_width=True, type="primary")

    if submitted:
        is_new_acct = 1 if m_acct_age < 30 else 0
        unusual_hr  = 1 if (m_hour < 6 or m_hour >= 23) else 0
        bal_util    = float(m_amount) / float(m_obal) if m_obal > 0 else 1.0
        bal_ratio   = float(m_obal) / float(m_amount) if m_amount > 0 else 10.0

        # Merge UPI auto-signals into ML features
        upi_sig       = upi_info.get("auto_signals", {})
        eff_new_rcpt  = max(int(m_new_rcpt), upi_sig.get("is_new_recipient", 0))
        eff_blacklist = max(int(m_black),    upi_sig.get("recipient_blacklisted", 0))
        eff_urgent    = max(int(m_urgent),   upi_sig.get("urgency_keywords_detected", 0))
        eff_new_acct  = max(is_new_acct,     upi_sig.get("is_new_account", 0))

        vr = 0
        if m_otp:          vr += 3
        if eff_new_acct:   vr += 2
        if unusual_hr:     vr += 2
        if eff_new_rcpt:   vr += 1
        if m_amount % 1000 == 0: vr += 1
        if m_vpn:          vr += 2
        if m_new_dev:      vr += 1
        if m_gift:         vr += 3
        if eff_urgent:     vr += 2
        if eff_blacklist:  vr += 3

        rf  = [eff_new_acct, int(m_new_dev), int(m_vpn), 0,
               unusual_hr, eff_new_rcpt, int(m_gift),
               int(m_otp), int(m_bio), 0, eff_blacklist, eff_urgent]
        ors = float(sum(rf)) / len(rf)

        txn = {
            "type": m_type, "amount": m_amount,
            "oldbalanceOrg": m_obal, "newbalanceOrig": m_nbal,
            "highAmountFlag": 1 if m_amount > 30000 else 0,
            "round_amount_flag": 1 if m_amount % 1000 == 0 else 0,
            "amount_just_below_threshold": 1 if m_amount in [4999,9999,19999,24999,29999,49999] else 0,
            "account_age_days": m_acct_age,   "is_new_account": eff_new_acct,
            "avg_txn_amount": 5000,            "txn_frequency_deviation": 1.0,
            "balance_utilization": bal_util,   "is_new_device": int(m_new_dev),
            "device_switch_count": 0,          "is_emulator": int(m_emul),
            "session_duration_anomaly": 0,     "multiple_sessions": 0,
            "ip_country_mismatch": 0,          "vpn_detected": int(m_vpn),
            "proxy_used": int(m_vpn),          "location_change_rate": 0.1,
            "unusual_location": 0,             "is_international": 0,
            "high_risk_country": 0,            "hour": m_hour,
            "day_of_week": 0,                  "unusual_hour_flag": unusual_hr,
            "time_since_last_txn": 30.0 if m_otp else 3600.0,
            "rapid_txn_flag": 1 if m_otp else 0,
            "otp_request_count": 5 if m_otp else 1, "otp_bypass_attempt": int(m_otp),
            "failed_auth_count": 2 if m_bio else 0, "biometric_failed": int(m_bio),
            "security_question_failed": 0,
            "is_new_recipient": eff_new_rcpt,  "recipient_blacklisted": eff_blacklist,
            "recipient_txn_count": 1 if eff_new_rcpt else 15,
            "same_recipient_rapid_txn": int(m_otp), "is_business_account": int(m_business),
            "high_risk_merchant": 0,           "gift_card_request": int(m_gift),
            "wire_to_new_account": 1 if (m_type == "TRANSFER" and eff_new_rcpt) else 0,
            "urgency_keywords_detected": eff_urgent, "shared_link_clicked": int(m_link),
            "third_party_involved": 0,         "phone_call_mentioned": 0,
            "balance_to_amount_ratio": bal_ratio,
            "amount_vs_avg_deviation": abs(float(m_amount) - 5000.0) / 5000.0,
            "unusually_small_txn": 1 if m_amount < 100 else 0,
            "consecutive_increasing_amounts": 0, "velocity_risk": vr,
            "overall_risk_score": round(ors, 2),
        }

        pred, prob = predict_txn(txn)
        # ── Contextual AI Intelligence Layer ──
        txn["upi_risk_score"] = upi_info.get("upi_risk_score", 0.0)
        ctx     = contextual_analysis(txn, prob)
        pct     = int(ctx["adjusted_prob"] * 100)
        raw_pct = int(ctx["raw_prob"] * 100)
        bar_col = score_color(pct)
        modifier_pct = int(abs(ctx["modifier"]) * 100)
        modifier_dir = "↓ reduced" if ctx["modifier"] < 0 else ("↑ raised" if ctx["modifier"] > 0 else "unchanged")
        modifier_col = "#00ff8c" if ctx["modifier"] < 0 else ("#ff8c00" if ctx["modifier"] > 0 else "#7aaace")

        # Pattern badges HTML
        pat_badges = ""
        for pat in ctx["patterns"]:
            meta = CTX_PATTERN_META.get(pat)
            if meta:
                col, label = meta
                pat_badges += (f'<span style="display:inline-block;font-size:0.68rem;font-weight:800;'
                               f'padding:4px 10px;border-radius:6px;margin:3px 4px 3px 0;'
                               f'background:{col}22;color:{col};border:1.5px solid {col}66;'
                               f'font-family:JetBrains Mono,monospace;letter-spacing:0.5px;">🔍 {label}</span>')

        # Build reasons — contextual AI reasons first, then UPI, then manual
        reasons = list(ctx["reasons"])   # contextual patterns go first
        for flag in upi_info.get("risk_flags", []):
            reasons.append(f"[UPI] {flag}")
        if not upi_input:
            reasons.append("[UPI] No UPI ID provided — recipient identity unverified")
        if m_otp:            reasons.append("OTP Bypass Attempt detected")
        if m_bio:            reasons.append("Biometric authentication failed")
        if m_vpn:            reasons.append("VPN / Proxy connection detected")
        if m_new_dev:        reasons.append("Transaction from new / unknown device")
        if m_gift:           reasons.append("Gift card payment requested")
        if eff_urgent:       reasons.append("Urgency language detected in communication")
        if m_link:           reasons.append("Phishing link was clicked")
        if eff_blacklist:    reasons.append("Recipient is on the blacklist")
        if eff_new_rcpt:     reasons.append("Sending to a brand-new / unverified recipient")
        if eff_new_acct:     reasons.append(f"Account is very new ({m_acct_age} days old)")
        if unusual_hr:       reasons.append(f"Unusual transaction hour ({m_hour}:00)")
        if m_amount > 30000: reasons.append(f"High-value transaction (₹{m_amount:,.0f})")
        if m_nbal == 0 and m_amount > 5000: reasons.append("Account balance completely drained to zero")
        if m_emul:           reasons.append("Emulator / virtual device detected")

        reasons_html = "<br>".join(f"• {r}" for r in reasons) if reasons \
                       else "• No significant risk factors detected."

        # UPI identity line shown inside result card
        if upi_input and upi_info["is_valid"]:
            upi_line = (
                f"<div style='margin-bottom:10px;padding:8px 12px;"
                f"background:rgba(0,200,255,0.07);border-radius:8px;"
                f"font-size:0.84rem;color:#8ba4d4;'>"
                f"Recipient UPI: <strong style='color:#e2f0ff;'>{upi_input.strip().lower()}</strong>"
                f" &nbsp;·&nbsp; Bank: <strong style='color:#00c8ff;'>@{upi_info['bank_vpa']}</strong></div>"
            )
        elif upi_input:
            upi_line = (
                f"<div style='margin-bottom:10px;font-size:0.84rem;color:#ff3d71;'>"
                f"⚠ Invalid UPI ID: <strong>{upi_input}</strong></div>"
            )
        else:
            upi_line = "<div style='margin-bottom:8px;font-size:0.8rem;color:#7aaace;'>No UPI ID provided</div>"

        if pct >= 80:
            card_cls = "result-fraud"
            icon     = "🚨"
            title    = "FRAUD DETECTED — DO NOT PROCEED"
            sub      = (f"XGBoost raw: <strong>{raw_pct}%</strong> &nbsp;→&nbsp; "
                        f"Contextual AI adjusted: <strong style='color:{bar_col};'>{pct}%</strong> "
                        f"<span style='color:{modifier_col};font-size:0.85em;'>({modifier_dir} {modifier_pct}% by situational analysis)</span>. "
                        f"Transaction should be <strong>BLOCKED IMMEDIATELY</strong>.")
        elif pct >= 40:
            card_cls = "result-suspicious"
            icon     = "⚠️"
            title    = "SUSPICIOUS — REVIEW CAREFULLY"
            sub      = (f"XGBoost raw: <strong>{raw_pct}%</strong> &nbsp;→&nbsp; "
                        f"Contextual AI adjusted: <strong style='color:{bar_col};'>{pct}%</strong> "
                        f"<span style='color:{modifier_col};font-size:0.85em;'>({modifier_dir} {modifier_pct}% by situational analysis)</span>. "
                        f"Requires <strong>manual review</strong> before proceeding.")
        else:
            card_cls = "result-safe"
            icon     = "✅"
            title    = "TRANSACTION APPEARS GENUINE"
            sub      = (f"XGBoost raw: <strong>{raw_pct}%</strong> &nbsp;→&nbsp; "
                        f"Contextual AI adjusted: <strong style='color:{bar_col};'>{pct}%</strong> "
                        f"<span style='color:{modifier_col};font-size:0.85em;'>({modifier_dir} {modifier_pct}% by situational analysis)</span>. "
                        f"Transaction appears <strong>LEGITIMATE</strong>.")

        # Contextual patterns block
        patterns_section = ""
        if pat_badges:
            patterns_section = f"""
<div style='margin:10px 0 6px 0;'>
<div style='font-size:0.65rem;font-weight:800;letter-spacing:0.15em;color:#7aaace;
font-family:JetBrains Mono,monospace;margin-bottom:6px;'>⚡ DETECTED PATTERNS</div>
{pat_badges}
</div>"""

        st.markdown(f"""
<div class="result-card {card_cls}">
<div class="result-title" style="color:{bar_col};">{icon} &nbsp;{title}</div>
{upi_line}
{patterns_section}
<div class="result-sub">{sub}</div>
<div class="result-bar-wrap">
<div class="result-bar-bg">
<div class="result-bar-fill" style="width:{pct}%;background:{bar_col};box-shadow:0 0 14px {bar_col}70;"></div>
</div>
<div class="result-bar-labels">
<span>0% — Genuine</span>
<span style="color:{bar_col};font-weight:800;">{pct}% Contextual Risk</span>
<span>100% — Confirmed Fraud</span>
</div>
</div>
<div class="result-reasons"><strong>AI Analysis &amp; Risk Factors:</strong><br>{reasons_html}</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="footer">FraudSense AI &nbsp;·&nbsp; Manual Payment Verification Engine &nbsp;·&nbsp; © 2026</div>',
                unsafe_allow_html=True)


# ─── MAIN APP SHELL ──────────────────────────────────────────────────────────
def main():
    # Inject global styles
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:16px 0 24px 0;">
            <div style="font-size:2.2rem;">🔐</div>
            <div style="font-size:1.1rem;font-weight:800;color:#e2f0ff;margin-top:4px;">FraudSense AI</div>
            <div style="font-size:0.7rem;color:#4a6888;letter-spacing:.12em;margin-top:2px;">FRAUD DETECTION SYSTEM</div>
        </div>""", unsafe_allow_html=True)

        page = st.radio(
            "Navigate",
            ["📡  Live Monitor", "🔍  Manual Checker"],
            label_visibility="collapsed",
        )

        st.markdown("""
        <div style="margin-top:32px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.07);">
            <div style="font-size:0.65rem;color:#6a92b8;letter-spacing:.1em;text-transform:uppercase;">System</div>
        </div>""", unsafe_allow_html=True)

        model_status = "✅ Model Loaded" if clf is not None else "❌ Model Missing"
        st.markdown(f'<div style="font-size:0.78rem;color:#00e896;margin-top:6px;">{model_status}</div>',
                    unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Reset Dashboard Data", use_container_width=True):
            for k in ["tx_feed", "al_feed", "seen_tx", "seen_al", "total", "fraud_cnt", "volume"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    if "Live Monitor" in page:
        page_live()
    else:
        page_checker()


if __name__ == "__main__":
    main()
