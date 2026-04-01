import json
import joblib
import os
import pandas as pd
from kafka import KafkaConsumer, KafkaProducer

# ── Load Model Bundle ─────────────────────────────────────────────────────────
MODEL_PATH = 'src/model/fraud_model.pkl'

if not os.path.exists(MODEL_PATH):
    print(f"Error: Model not found at {MODEL_PATH}. Please run src/model/train.py first.")
    exit(1)

print("Loading XGBoost model...")
bundle = joblib.load(MODEL_PATH)
clf = bundle['model']
FEATURE_COLS = bundle['features']
print(f"Model loaded. Features ({len(FEATURE_COLS)}): {FEATURE_COLS[:10]}...")

# ── Kafka Setup ───────────────────────────────────────────────────────────────
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')

consumer = KafkaConsumer(
    'transactions',
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='latest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# ── Type mapping ───────────────────────────────────────────────────────────────
TYPE_MAP = {'PAYMENT': 0, 'TRANSFER': 1, 'CASH_OUT': 2, 'DEBIT': 3, 'CASH_IN': 4}

print("FraudSense AI Detector started — analyzing with behavioral biometrics...")

for message in consumer:
    txn = message.value

    tx_type_str = txn.get('type', '')
    if tx_type_str not in TYPE_MAP:
        continue

    amount = txn.get('amount', 0)
    old_balance_org = txn.get('oldbalanceOrg', 0)
    new_balance_org = txn.get('newbalanceOrig', 0)
    balance_diff = old_balance_org - new_balance_org

    # ── Build all features from transaction ──
    features_dict = {
        'type': TYPE_MAP[tx_type_str],
        'amount': amount,
        'oldbalanceOrg': old_balance_org,
        'newbalanceOrig': new_balance_org,
        'balanceDiff': balance_diff,
        'highAmountFlag': 1 if amount > 30000 else 0,
        'round_amount_flag': txn.get('round_amount_flag', 0),
        'amount_just_below_threshold': txn.get('amount_just_below_threshold', 0),
        'account_age_days': txn.get('account_age_days', 500),
        'is_new_account': txn.get('is_new_account', 0),
        'avg_txn_amount': txn.get('avg_txn_amount', 5000),
        'txn_frequency_deviation': txn.get('txn_frequency_deviation', 1.0),
        'balance_utilization': txn.get('balance_utilization', 0.5),
        'is_new_device': txn.get('is_new_device', 0),
        'device_switch_count': txn.get('device_switch_count', 0),
        'is_emulator': txn.get('is_emulator', 0),
        'session_duration_anomaly': txn.get('session_duration_anomaly', 0),
        'multiple_sessions': txn.get('multiple_sessions', 0),
        'ip_country_mismatch': txn.get('ip_country_mismatch', 0),
        'vpn_detected': txn.get('vpn_detected', 0),
        'proxy_used': txn.get('proxy_used', 0),
        'location_change_rate': txn.get('location_change_rate', 0.1),
        'unusual_location': txn.get('unusual_location', 0),
        'is_international': txn.get('is_international', 0),
        'high_risk_country': txn.get('high_risk_country', 0),
        'hour': txn.get('hour', 12),
        'day_of_week': txn.get('day_of_week', 0),
        'unusual_hour_flag': txn.get('unusual_hour_flag', 0),
        'time_since_last_txn': txn.get('time_since_last_txn', 3600),
        'rapid_txn_flag': txn.get('rapid_txn_flag', 0),
        'otp_request_count': txn.get('otp_request_count', 1),
        'otp_bypass_attempt': txn.get('otp_bypass_attempt', 0),
        'failed_auth_count': txn.get('failed_auth_count', 0),
        'biometric_failed': txn.get('biometric_failed', 0),
        'security_question_failed': txn.get('security_question_failed', 0),
        'is_new_recipient': txn.get('is_new_recipient', 0),
        'recipient_blacklisted': txn.get('recipient_blacklisted', 0),
        'recipient_txn_count': txn.get('recipient_txn_count', 10),
        'same_recipient_rapid_txn': txn.get('same_recipient_rapid_txn', 0),
        'is_business_account': txn.get('is_business_account', 0),
        'high_risk_merchant': txn.get('high_risk_merchant', 0),
        'gift_card_request': txn.get('gift_card_request', 0),
        'wire_to_new_account': txn.get('wire_to_new_account', 0),
        'urgency_keywords_detected': txn.get('urgency_keywords_detected', 0),
        'shared_link_clicked': txn.get('shared_link_clicked', 0),
        'third_party_involved': txn.get('third_party_involved', 0),
        'phone_call_mentioned': txn.get('phone_call_mentioned', 0),
        'balance_to_amount_ratio': txn.get('balance_to_amount_ratio', 10.0),
        'amount_vs_avg_deviation': txn.get('amount_vs_avg_deviation', 0.5),
        'unusually_small_txn': txn.get('unusually_small_txn', 0),
        'consecutive_increasing_amounts': txn.get('consecutive_increasing_amounts', 0),
        'velocity_risk': txn.get('velocity_risk', 0),
        'overall_risk_score': txn.get('overall_risk_score', 0.1),
    }

    # Build DataFrame with correct column order
    features = pd.DataFrame([features_dict], columns=FEATURE_COLS)

    prediction = clf.predict(features)[0]
    prob = float(clf.predict_proba(features)[0][1])

    # ── Build Alert Reasons ──
    alert_reasons = []
    risk_level = "LOW"
    
    if txn.get('otp_bypass_attempt'):
        alert_reasons.append("OTP BYPASS")
        risk_level = "HIGH"
    if txn.get('gift_card_request'):
        alert_reasons.append("GIFT CARD REQUEST")
        risk_level = "HIGH"
    if txn.get('urgency_keywords_detected'):
        alert_reasons.append("URGENCY DETECTED")
        risk_level = "HIGH"
    if txn.get('vpn_detected'):
        alert_reasons.append("VPN/PROXY")
        risk_level = "MEDIUM"
    if txn.get('is_new_account'):
        alert_reasons.append("NEW ACCOUNT")
    if txn.get('is_new_device'):
        alert_reasons.append("NEW DEVICE")
    if txn.get('is_emulator'):
        alert_reasons.append("EMULATOR DETECTED")
        risk_level = "HIGH"
    if txn.get('is_new_recipient'):
        alert_reasons.append("NEW RECIPIENT")
    if txn.get('recipient_blacklisted'):
        alert_reasons.append("BLACKLISTED RECIPIENT")
        risk_level = "HIGH"
    if txn.get('unusual_hour_flag'):
        alert_reasons.append("UNUSUAL HOUR")
    if txn.get('rapid_txn_flag'):
        alert_reasons.append("RAPID TRANSACTION")
    if txn.get('biometric_failed'):
        alert_reasons.append("BIOMETRIC FAILED")
        risk_level = "HIGH"
    if txn.get('third_party_involved'):
        alert_reasons.append("THIRD PARTY")
    if txn.get('shared_link_clicked'):
        alert_reasons.append("PHISHING LINK")
        risk_level = "HIGH"
    if txn.get('wire_to_new_account'):
        alert_reasons.append("WIRE TO NEW ACCT")
    if txn.get('phone_call_mentioned'):
        alert_reasons.append("PHONE SCAM")
        risk_level = "HIGH"
    if txn.get('high_risk_country'):
        alert_reasons.append("HIGH-RISK COUNTRY")
        risk_level = "MEDIUM"
    if txn.get('session_duration_anomaly'):
        alert_reasons.append("SHORT SESSION")
    if new_balance_org == 0 and amount > 5000:
        alert_reasons.append("ACCOUNT DRAINING")
    if amount > 30000:
        alert_reasons.append("HIGH AMOUNT")

    if prediction == 1:
        reason_text = " | ".join(alert_reasons) if alert_reasons else f"Fraud Score: {prob:.2f}"
        print(f"[FRAUD] Txn: {txn['transactionId']} | Score: {prob:.2f} | {reason_text}")
        
        alert = {
            'transactionId': txn['transactionId'],
            'status': 'BLOCKED',
            'reason': reason_text,
            'score': round(prob, 3),
            'risk_level': risk_level,
            'original_txn': txn
        }
        producer.send('fraud_alerts', alert)
    else:
        print(f"[SAFE]  Txn: {txn['transactionId']} | Score: {prob:.2f}")
