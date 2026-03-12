import streamlit as st
import json
from kafka import KafkaConsumer
import time
import os

# ─── 0. PAGE CONFIG (MUST BE FIRST) ───────────────────────────────────────────
st.set_page_config(
    page_title="Digital Payment Fraud Detection",
    page_icon="🔐",
    layout="wide"
)


# ─── 1. KAFKA CONNECTION ───────────────────────────────────────────────────────
BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

@st.cache_resource
def get_kafka_streams():
    ts = int(time.time())
    try:
        tx = KafkaConsumer(
            "transactions",
            bootstrap_servers=BROKER,
            auto_offset_reset="latest",
            value_deserializer=lambda x: json.loads(x.decode()),
            group_id=f"utx_{ts}",
            consumer_timeout_ms=150
        )
        al = KafkaConsumer(
            "fraud_alerts",
            bootstrap_servers=BROKER,
            auto_offset_reset="latest",
            value_deserializer=lambda x: json.loads(x.decode()),
            group_id=f"ual_{ts}",
            consumer_timeout_ms=150
        )
        return tx, al, True
    except Exception:
        return None, None, False


def main():
    # ─── 2. INJECT CSS (once via cache) ──────────────────────────────────────
    @st.cache_data(show_spinner=False)
    def load_css():
        try:
            with open("src/dashboard/style.css") as f:
                return f.read()
        except Exception:
            return ""

    css = load_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    # ─── 3. SESSION STATE INIT ────────────────────────────────────────────────
    if "tx_feed"    not in st.session_state: st.session_state.tx_feed    = []
    if "al_feed"    not in st.session_state: st.session_state.al_feed    = []
    if "seen_ids"   not in st.session_state: st.session_state.seen_ids   = set()
    if "total"      not in st.session_state: st.session_state.total      = 0
    if "fraud_cnt"  not in st.session_state: st.session_state.fraud_cnt  = 0
    if "volume"     not in st.session_state: st.session_state.volume     = 0.0
    if "kafka_ok"   not in st.session_state: st.session_state.kafka_ok   = True

    # ─── 4. PULL KAFKA MESSAGES ───────────────────────────────────────────────
    t_s, a_s, connected = get_kafka_streams()
    st.session_state.kafka_ok = connected

    if connected:
        for m in t_s:
            v  = m.value
            tid = v.get("transactionId", "")
            if tid and tid not in st.session_state.seen_ids:
                st.session_state.seen_ids.add(tid)
                st.session_state.tx_feed.append(v)
                st.session_state.total  += 1
                st.session_state.volume += v.get("amount", 0)

        for m in a_s:
            v   = m.value
            tid = v.get("transactionId", "")
            if tid and tid not in st.session_state.seen_ids:
                st.session_state.seen_ids.add(tid + "_alert")
                st.session_state.al_feed.append(v)
                st.session_state.fraud_cnt += 1

    # Keep only latest N items in feed memory
    st.session_state.tx_feed = st.session_state.tx_feed[-200:]
    st.session_state.al_feed = st.session_state.al_feed[-100:]

    total     = st.session_state.total
    fraud_cnt = st.session_state.fraud_cnt
    volume    = st.session_state.volume
    safety    = max(0.0, 100.0 - (fraud_cnt / max(total, 1) * 100))
    fraud_pct = min(100, (fraud_cnt / max(total, 1)) * 100)

    # ─── 5. HEADER ────────────────────────────────────────────────────────────
    kafka_status_html = (
        '<span class="status-dot online"></span><span class="status-text">LIVE</span>'
        if st.session_state.kafka_ok else
        '<span class="status-dot offline"></span><span class="status-text">KAFKA OFFLINE</span>'
    )

    st.markdown(f"""
    <div class="hero">
        <div class="hero-left">
            <div class="hero-tag">🛡️ &nbsp;AI SECURITY SYSTEM &nbsp;·&nbsp; REAL-TIME MONITORING</div>
            <h1 class="hero-title">GuardianAI</h1>
            <div class="hero-sub">Digital Payment Fraud Detection Platform</div>
        </div>
        <div class="hero-right">
            <div class="live-pill">{kafka_status_html}</div>
            <div class="ts-label">Last refresh: {time.strftime('%H:%M:%S')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── 6. KPI CARDS ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi">
            <div class="kpi-icon">📥</div>
            <div class="kpi-num">{total:,}</div>
            <div class="kpi-lbl">Transactions Processed</div>
            <div class="kpi-accent cyan"></div>
        </div>
        <div class="kpi">
            <div class="kpi-icon">🚨</div>
            <div class="kpi-num red">{fraud_cnt:,}</div>
            <div class="kpi-lbl">Fraud Alerts</div>
            <div class="kpi-accent red"></div>
        </div>
        <div class="kpi">
            <div class="kpi-icon">🛡️</div>
            <div class="kpi-num green">{safety:.1f}%</div>
            <div class="kpi-lbl">System Safety Score</div>
            <div class="kpi-bar-bg">
                <div class="kpi-bar-fill green" style="width:{safety:.1f}%"></div>
            </div>
            <div class="kpi-accent green"></div>
        </div>
        <div class="kpi">
            <div class="kpi-icon">💰</div>
            <div class="kpi-num amber">${volume/1000:,.1f}K</div>
            <div class="kpi-lbl">Volume Monitored</div>
            <div class="kpi-accent amber"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── 7. SYSTEM RISK GAUGE ─────────────────────────────────────────────────
    risk_label = "LOW RISK" if fraud_pct < 5 else ("MEDIUM RISK" if fraud_pct < 15 else "HIGH RISK")
    risk_color = "#00e396"  if fraud_pct < 5 else ("#f5ae0b"   if fraud_pct < 15 else "#ff3d71")
    st.markdown(f"""
    <div class="risk-gauge-wrap">
        <div class="rg-left">
            <span class="rg-label">SYSTEM RISK LEVEL</span>
            <span class="rg-badge" style="color:{risk_color}; border-color:{risk_color}30;">{risk_label}</span>
        </div>
        <div class="rg-bar-bg">
            <div class="rg-bar-fill" style="width:{fraud_pct:.2f}%; background:{risk_color}; box-shadow: 0 0 12px {risk_color}80;"></div>
        </div>
        <span class="rg-pct" style="color:{risk_color};">{fraud_pct:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)

    # ─── 8. DIVIDER ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ─── 9. DUAL PANEL LAYOUT ─────────────────────────────────────────────────
    col1, col2 = st.columns(2, gap="large")

    # ── LEFT: TRANSACTION STREAM ──
    with col1:
        hd_col, flt_col = st.columns([3, 1])
        with hd_col:
            st.markdown("""
            <div class="panel-title cyan">
                <span class="panel-icon">⟳</span> PAYMENT STREAM
                <div class="p-line"></div>
            </div>""", unsafe_allow_html=True)
        with flt_col:
            tx_filter = st.selectbox(
                "filter",
                ["ALL", "CASH_OUT", "TRANSFER", "PAYMENT", "CASH_IN", "DEBIT"],
                label_visibility="collapsed",
                key="tx_filter"
            )

        feed = list(reversed(st.session_state.tx_feed))
        if tx_filter != "ALL":
            feed = [x for x in feed if x.get("type") == tx_filter]

        # Build scroll box HTML
        rows_html = ""
        if not feed:
            rows_html = '<div class="empty-state">📡 No transactions yet — waiting for stream...</div>'
        else:
            for t in feed:
                amt      = t.get("amount", 0)
                t_type   = t.get("type", "TXN")
                ts_raw   = t.get("timestamp", "")
                ts_time  = ts_raw[11:19] if len(ts_raw) >= 19 else "—"
                tid      = t.get("transactionId", "—")[-8:]
                sender   = t.get("nameOrig", "—")
                receiver = t.get("nameDest", "—")
                # Sliding bar: normalize amount 0–50000
                bar_pct  = min(100, (amt / 50000) * 100)
                rows_html += f"""
                <div class="tx-row">
                    <div class="tx-top">
                        <div class="tx-left">
                            <span class="type-pill">{t_type}</span>
                            <span class="tx-id">#{tid}</span>
                        </div>
                        <div class="tx-amt">${amt:,.0f}</div>
                    </div>
                    <div class="tx-people">
                        <span class="tx-person">↑ {sender[:20]}</span>
                        <span class="tx-arrow">→</span>
                        <span class="tx-person">{receiver[:20]}</span>
                        <span class="tx-ts">{ts_time}</span>
                    </div>
                    <div class="slide-bar-bg">
                        <div class="slide-bar-fill cyan" style="width:{bar_pct:.1f}%"></div>
                    </div>
                </div>"""

        st.markdown(f'<div class="scroll-box">{rows_html}</div>', unsafe_allow_html=True)

    # ── RIGHT: FRAUD / THREAT PANEL ──
    with col2:
        st.markdown(f"""
        <div class="panel-title red">
            <span class="panel-icon">⚠</span> THREAT INTELLIGENCE
            <span class="panel-count">({fraud_cnt} alerts)</span>
            <div class="p-line red-line"></div>
        </div>""", unsafe_allow_html=True)

        alerts = list(reversed(st.session_state.al_feed))

        al_rows = ""
        if not alerts:
            al_rows = '<div class="empty-state green">🛡️ All Clear — No threats detected. Scanning active...</div>'
        else:
            for a in alerts:
                o    = a.get("original_txn", {})
                sc   = a.get("score", 0.95)
                amt  = o.get("amount", 0)
                typ  = o.get("type", "FRAUD")
                tid  = o.get("transactionId", "—")[-8:]
                ts_r = o.get("timestamp", "")
                ts_t = ts_r[11:19] if len(ts_r) >= 19 else "—"
                sender   = o.get("nameOrig", "—")
                receiver = o.get("nameDest", "—")
                sc_pct   = int(sc * 100)
                # Score colour gradient
                sc_col   = "#ff3d71" if sc_pct > 80 else ("#f5ae0b" if sc_pct > 50 else "#00e396")
                al_rows += f"""
                <div class="al-row">
                    <div class="al-top">
                        <div class="al-left">
                            <span class="type-pill red">⚠ {typ}</span>
                            <span class="tx-id red">#{tid}</span>
                        </div>
                        <div class="tx-amt red">${amt:,.0f}</div>
                    </div>
                    <div class="tx-people">
                        <span class="tx-person">↑ {sender[:20]}</span>
                        <span class="tx-arrow">→</span>
                        <span class="tx-person">{receiver[:20]}</span>
                        <span class="tx-ts">{ts_t}</span>
                    </div>
                    <div class="al-score-row">
                        <span class="al-score-lbl">FRAUD SCORE</span>
                        <div class="slide-bar-bg">
                            <div class="slide-bar-fill fraud" style="width:{sc_pct}%; background:{sc_col}; box-shadow: 0 0 8px {sc_col}80;"></div>
                        </div>
                        <span class="al-score-pct" style="color:{sc_col};">{sc_pct}%</span>
                    </div>
                </div>"""

        st.markdown(f'<div class="scroll-box alert-box">{al_rows}</div>', unsafe_allow_html=True)

    # ─── 10. FOOTER ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="footer">
        GuardianAI · Digital Payment Fraud Detection · Powered by Apache Kafka &amp; Random Forest ML
        &nbsp;|&nbsp; {time.strftime('%Y-%m-%d')}
    </div>
    """, unsafe_allow_html=True)

    # ─── 11. AUTO-REFRESH ────────────────────────────────────────────────────
    time.sleep(1)
    st.rerun()


if __name__ == "__main__":
    main()
