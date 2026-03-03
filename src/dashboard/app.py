import streamlit as st
import json
from kafka import KafkaConsumer
import pandas as pd
import time
import subprocess
import os
import signal
import psutil
import requests

# --- Page Config ---
st.set_page_config(
    page_title="GuardianAI | Secure Monitor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Lottie Animation Loader ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# --- Process Management Logic ---
PID_FILE = ".producer_pid"

def is_producer_running():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                return True, pid
            else:
                return False, None
        except:
            return False, None
    return False, None

def start_producer():
    if is_producer_running()[0]:
        st.toast("Simulation is already running!", icon="⚠️")
        return

    # Start process
    proc = subprocess.Popen(
        ["python", "src/producer/app.py"], 
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    # Save PID
    with open(PID_FILE, 'w') as f:
        f.write(str(proc.pid))
    
    st.toast("Simulation Started Successfully!", icon="🚀")
    time.sleep(1)
    st.rerun()

def stop_producer():
    running, pid = is_producer_running()
    if running and pid:
        try:
            p = psutil.Process(pid)
            p.terminate() 
            p.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            try:
                os.kill(pid, signal.SIGTERM)
            except:
                pass
        
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            
        st.toast("Simulation Stopped Safely.", icon="🛑")
        time.sleep(1)
        st.rerun()
    else:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        st.toast("No active simulation found.", icon="ℹ️")
        st.rerun()

# --- CSS Loader ---
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file not found: {file_name}")

load_css("src/dashboard/style.css")

# --- UI Header & Animation ---
col_anim, col_title, col_actions = st.columns([1, 3, 1.5])

with col_anim:
    # Use a secure shield lottie animation
    try:
        from streamlit_lottie import st_lottie
        lottie_security = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_m9zragwd.json")
        if lottie_security:
            st_lottie(lottie_security, height=100, key="security_anim")
        else:
            st.markdown("<h1>🛡️</h1>", unsafe_allow_html=True)
    except ImportError:
        st.markdown("<h1>🛡️</h1>", unsafe_allow_html=True)

with col_title:
    st.markdown("""
    <div style="padding-top: 10px;">
        <h1 style="margin-bottom: 0;">GuardianAI Monitor</h1>
        <p style="color: #64748b; font-size: 1.1rem; margin-top: 5px;">Real-Time Financial Security System</p>
    </div>
    """, unsafe_allow_html=True)

with col_actions:
    st.markdown("<br>", unsafe_allow_html=True)
    running, _ = is_producer_running()
    if running:
        if st.button("🛑 STOP STREAM", type="primary", use_container_width=True):
            stop_producer()
        st.markdown("<div style='text-align:center; color:#10b981; font-weight:600; font-size:0.8rem; margin-top:5px;'>● LIVE MONITORING</div>", unsafe_allow_html=True)
    else:
        if st.button("⚡ START STREAM", use_container_width=True):
            start_producer()
        st.markdown("<div style='text-align:center; color:#94a3b8; font-weight:600; font-size:0.8rem; margin-top:5px;'>● SYSTEM OFFLINE</div>", unsafe_allow_html=True)

st.markdown("---")

# --- Metrics Section ---
placeholder_metrics = st.empty()

# --- Content Grid ---
col_main, col_side = st.columns([2, 1.2])

with col_main:
    st.markdown("#### 📡 Live Transaction Feed")
    tx_table_placeholder = st.empty()

with col_side:
    st.markdown("#### 🚨 Threat & Fraud Log")
    alert_feed_placeholder = st.empty()

# --- Kafka Setup ---
def get_consumers():
    try:
        ts = int(time.time())
        c_tx = KafkaConsumer(
            'transactions',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='latest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id=f'ui_tx_{ts}',
            consumer_timeout_ms=300
        )
        c_alert = KafkaConsumer(
            'fraud_alerts',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='latest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id=f'ui_alert_{ts}',
            consumer_timeout_ms=100
        )
        return c_tx, c_alert
    except Exception:
        return None, None

consumer_tx, consumer_alert = get_consumers()

if not consumer_tx:
    st.error("Backend Disconnected. Start Docker Services.")
    st.info("Attempting to connect to Kafka at localhost:9092...")
    try:
        from kafka import KafkaAdminClient
        client = KafkaAdminClient(bootstrap_servers='localhost:9092')
        st.success("Successfully connected to Kafka Admin Client!")
        client.close()
    except Exception as e:
        st.error(f"Failed to connect to Kafka: {e}")
    st.stop()

st.success("Successfully connected to Kafka topics.")

# State
transactions = []
alerts = []
stats = {"total": 0, "fraud": 0, "amount_checked": 0}

while True:
    # Read Kafka
    batch_tx = []
    for m in consumer_tx:
        batch_tx.append(m.value)
        stats["total"] += 1
        stats["amount_checked"] += m.value.get("amount", 0)
    
    batch_alert = []
    for m in consumer_alert:
        batch_alert.append(m.value)
        stats["fraud"] += 1

    # Buffer updates
    if batch_tx:
        transactions.extend(batch_tx)
        transactions = transactions[-15:] # Keep last 15
    
    if batch_alert:
        alerts.extend(batch_alert)
        alerts = alerts[-10:] # Keep last 10
    
    fraud_rate = (stats["fraud"] / stats["total"] * 100) if stats["total"] > 0 else 0
    
    # Render KPI Cards
    with placeholder_metrics.container():
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;">
            <div class="kpi-card">
                <div class="kpi-label">Total Volume</div>
                <div class="kpi-value">{stats['total']:,}</div>
                <div class="kpi-sub">Transactions</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Blocked Threats</div>
                <div class="kpi-value" style="color: var(--danger);">{stats['fraud']}</div>
                <div class="kpi-sub">High Risk</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Safety Score</div>
                <div class="kpi-value" style="color: var(--success);">{100 - fraud_rate:.1f}%</div>
                <div class="kpi-sub">System Health</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Avg Value</div>
                <div class="kpi-value">${(stats['amount_checked']/stats['total'] if stats['total'] else 0):.0f}</div>
                <div class="kpi-sub">Per Txn</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Render Table
    with tx_table_placeholder:
        if transactions:
            df = pd.DataFrame(transactions)
            
            # --- RoBust Column Selection ---
            # Ensure columns exist, fallback if not
            cols_map = {
                'transactionId': 'Transaction ID', 
                'timestamp': 'Time',
                'type': 'Type', 
                'amount': 'Amount'
            }
            
            available_cols = [c for c in cols_map.keys() if c in df.columns]
            
            if available_cols:
                df_display = df[available_cols].copy()
                df_display.rename(columns=cols_map, inplace=True)
                
                # Format currency if Amount exists
                if 'Amount' in df_display.columns:
                    df_display['Amount'] = df_display['Amount'].apply(lambda x: f"${x:,.2f}")
                
                st.dataframe(
                    df_display.iloc[::-1], 
                    use_container_width=True,
                    hide_index=True 
                )
            else:
                st.write(df.iloc[::-1]) # Fallback to raw
        else:
            st.info("Waiting for transaction stream...")

    # Render Alerts
    with alert_feed_placeholder.container():
        if alerts:
            for a in reversed(alerts):
                # Safely get transaction details from alert
                original_txn = a.get('original_txn', {})
                amount = original_txn.get('amount', 0)
                score = a.get('score', 0.99)
                
                st.markdown(f"""
                <div class="alert-banner">
                    <div>
                        <div style="font-weight:700; color:#b91c1c;">🚫 FRAUD BLOCKED</div>
                        <div style="font-size:0.8rem; color:#6b7280;">ID: {a.get('transactionId', 'N/A')}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-weight:600;">${amount:,.2f}</div>
                        <div style="font-size:0.75rem; color:#ef4444;">Risk: {score:.2f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 30px; opacity: 0.7;">
                <div style="font-size: 3rem;">🛡️</div>
                <p>No active threats</p>
            </div>
            """, unsafe_allow_html=True)

    time.sleep(0.5)
