import os
import json
import time
import random
from kafka import KafkaProducer
import numpy as np
from datetime import datetime
from faker import Faker

def sanitize(obj):
    """Recursively convert numpy scalar types to native Python so JSON serialisation never fails."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(i) for i in obj]
    if isinstance(obj, np.integer):   return int(obj)
    if isinstance(obj, np.floating):  return float(obj)
    if isinstance(obj, np.bool_):     return bool(obj)
    if isinstance(obj, np.ndarray):   return obj.tolist()
    return obj

fake = Faker()

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')

def get_producer():
    max_retries = 10
    for i in range(max_retries):
        try:
            return KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except Exception as e:
            print(f"Waiting for Kafka... (Attempt {i+1}/{max_retries})")
            time.sleep(5)
    raise Exception("Could not connect to Kafka")

producer = get_producer()
TOPIC_NAME = 'transactions'

# Risk configurations
HIGH_RISK_COUNTRIES = ['Nigeria', 'Ghana', 'Kenya', 'Pakistan', 'Bangladesh']
SCAM_LOCATIONS = ['Delhi', 'Mumbai', 'Kolkata']
HIGH_RISK_HOURS = list(range(0, 6))
GIFT_CARD_MERCHANTS = ['Amazon', 'Google Play', 'Apple', 'Steam', 'Microsoft']

def generate_transaction():
    """
    Generates realistic transactions with comprehensive behavioral features.
    Based on real fraud patterns from research.
    """
    is_fraudster = np.random.random() < 0.12  # 12% fraudsters
    
    # ── Account Age ──
    if is_fraudster:
        account_age_days = np.random.randint(1, 60)
    else:
        account_age_days = np.random.randint(30, 2000)
    is_new_account = 1 if account_age_days < 30 else 0
    
    # ── Transaction Type ──
    if is_fraudster:
        tx_type = np.random.choice(['TRANSFER', 'CASH_OUT', 'PAYMENT'], p=[0.5, 0.3, 0.2])
    else:
        tx_type = np.random.choice(['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT', 'CASH_IN'])
    
    # ── Amount ──
    if is_fraudster and np.random.random() < 0.25:
        amount = round(np.random.choice([1000, 2000, 5000, 10000, 15000, 20000, 49900]), 2)
    elif is_fraudster and np.random.random() < 0.2:
        amount = round(np.random.choice([4999, 9999, 19999, 24999, 29999, 49999]), 2)
    else:
        amount = round(np.random.uniform(10, 50000), 2)
    
    round_amount_flag = 1 if amount % 1000 == 0 else 0
    amount_just_below_threshold = 1 if amount in [4999, 9999, 19999, 24999, 29999, 49999] else 0
    
    # ── Balance ──
    if is_new_account:
        old_balance_org = round(np.random.choice([5000, 10000, 20000, 50000]), 2)
    else:
        old_balance_org = round(np.random.uniform(500, 100000), 2)
    
    if is_fraudster and tx_type in ['CASH_OUT', 'TRANSFER']:
        if np.random.random() < 0.85:
            new_balance_org = 0
        else:
            new_balance_org = max(0, old_balance_org - amount)
    else:
        new_balance_org = max(0, old_balance_org - amount)
    
    # ── Account Behavior ──
    avg_txn_amount = round(np.random.uniform(500, 50000), 2)
    amount_vs_avg_deviation = abs(amount - avg_txn_amount) / avg_txn_amount if avg_txn_amount > 0 else 0
    txn_frequency_deviation = np.random.uniform(0.1, 5.0) if is_fraudster else np.random.uniform(0.1, 1.5)
    balance_utilization = amount / old_balance_org if old_balance_org > 0 else 1
    
    # ── Device Features ──
    if is_fraudster:
        is_new_device = np.random.choice([0, 1], p=[0.3, 0.7])
        is_emulator = np.random.choice([0, 1], p=[0.4, 0.6])
        device_switch_count = np.random.randint(0, 5)
    else:
        is_new_device = np.random.choice([0, 1], p=[0.8, 0.2])
        is_emulator = 0
        device_switch_count = np.random.randint(0, 2)
    
    # ── Session ──
    session_duration_anomaly = 1 if (is_fraudster and np.random.random() < 0.8) else 0
    multiple_sessions = 1 if (is_fraudster and np.random.random() < 0.7) else 0
    
    # ── Network ──
    if is_fraudster:
        vpn_detected = np.random.choice([0, 1], p=[0.2, 0.8])
        proxy_used = np.random.choice([0, 1], p=[0.3, 0.7])
        ip_country_mismatch = np.random.choice([0, 1], p=[0.4, 0.6])
        high_risk_country = np.random.choice([0, 1], p=[0.3, 0.7])
    else:
        vpn_detected = np.random.choice([0, 1], p=[0.95, 0.05])
        proxy_used = np.random.choice([0, 1], p=[0.98, 0.02])
        ip_country_mismatch = 0
        high_risk_country = np.random.choice([0, 1], p=[0.95, 0.05])
    
    # ── Location ──
    locations = ['Hyderabad', 'Bangalore', 'Chennai', 'Delhi', 'Mumbai', 'Kolkata']
    location = np.random.choice(locations)
    unusual_location = 1 if location in SCAM_LOCATIONS else 0
    location_change_rate = np.random.uniform(0.5, 1.0) if is_fraudster else np.random.uniform(0, 0.3)
    is_international = np.random.choice([0, 0, 0, 1])
    
    # ── Time ──
    if is_fraudster:
        # 7 choices (0,1,2,3,4,5,23) — probabilities must sum to 1.0
        hour = np.random.choice(list(range(0, 6)) + [23], p=[0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.10])
    else:
        hour = np.random.randint(6, 23)
    
    day_of_week = np.random.randint(0, 7)
    unusual_hour_flag = 1 if hour in HIGH_RISK_HOURS else 0
    time_since_last_txn = np.random.uniform(0, 60) if is_fraudster else np.random.uniform(60, 86400)
    rapid_txn_flag = 1 if time_since_last_txn < 60 else 0
    
    # ── Authentication ──
    if is_fraudster:
        otp_request_count = np.random.randint(2, 10)
        otp_bypass_attempt = np.random.choice([0, 1], p=[0.3, 0.7])
        failed_auth_count = np.random.randint(1, 5)
        biometric_failed = np.random.choice([0, 1], p=[0.2, 0.8])
        security_question_failed = np.random.choice([0, 1], p=[0.3, 0.7])
    else:
        otp_request_count = np.random.randint(1, 3)
        otp_bypass_attempt = 0
        failed_auth_count = np.random.randint(0, 2)
        biometric_failed = np.random.choice([0, 1], p=[0.98, 0.02])
        security_question_failed = np.random.choice([0, 1], p=[0.99, 0.01])
    
    # ── Recipient ──
    if is_fraudster:
        is_new_recipient = np.random.choice([0, 1], p=[0.1, 0.9])
        recipient_blacklisted = np.random.choice([0, 1], p=[0.4, 0.6])
    else:
        is_new_recipient = np.random.choice([0, 1], p=[0.7, 0.3])
        recipient_blacklisted = np.random.choice([0, 1], p=[0.99, 0.01])
    
    recipient_txn_count = np.random.randint(1, 50)
    same_recipient_rapid_txn = 1 if (rapid_txn_flag and is_new_recipient) else 0
    
    merchant = fake.company()
    is_business_account = np.random.choice([0, 1])
    high_risk_merchant = 1 if any(gc in merchant for gc in GIFT_CARD_MERCHANTS) else 0
    
    # ── Social Engineering Indicators ──
    if is_fraudster:
        gift_card_request = np.random.choice([0, 1], p=[0.4, 0.6])
        wire_to_new_account = np.random.choice([0, 1], p=[0.3, 0.7])
        urgency_keywords_detected = np.random.choice([0, 1], p=[0.2, 0.8])
        shared_link_clicked = np.random.choice([0, 1], p=[0.3, 0.7])
        third_party_involved = np.random.choice([0, 1], p=[0.4, 0.6])
        phone_call_mentioned = np.random.choice([0, 1], p=[0.5, 0.5])
    else:
        gift_card_request = 0
        wire_to_new_account = 0
        urgency_keywords_detected = np.random.choice([0, 1], p=[0.95, 0.05])
        shared_link_clicked = np.random.choice([0, 1], p=[0.98, 0.02])
        third_party_involved = np.random.choice([0, 1], p=[0.95, 0.05])
        phone_call_mentioned = np.random.choice([0, 1], p=[0.99, 0.01])
    
    # ── Amount Patterns ──
    balance_to_amount_ratio = old_balance_org / amount if amount > 0 else 10
    unusually_small_txn = 1 if (amount < 100 and is_fraudster) else 0
    consecutive_increasing_amounts = 1 if (is_fraudster and np.random.random() < 0.7) else 0
    
    # ── Risk Scores ──
    velocity_risk = 0
    if rapid_txn_flag: velocity_risk += 3
    if is_new_account: velocity_risk += 2
    if unusual_hour_flag: velocity_risk += 2
    if is_new_recipient: velocity_risk += 1
    if round_amount_flag: velocity_risk += 1
    if vpn_detected: velocity_risk += 2
    if is_new_device: velocity_risk += 1
    if otp_bypass_attempt: velocity_risk += 3
    if gift_card_request: velocity_risk += 3
    if urgency_keywords_detected: velocity_risk += 2
    
    risk_factors = [is_new_account, is_new_device, vpn_detected, proxy_used,
                    unusual_hour_flag, is_new_recipient, gift_card_request,
                    otp_bypass_attempt, biometric_failed, high_risk_country,
                    recipient_blacklisted, urgency_keywords_detected]
    overall_risk_score = sum(risk_factors) / len(risk_factors)
    
    # ── Timestamp ──
    dt = datetime.now().replace(hour=hour, minute=np.random.randint(0, 60), second=np.random.randint(0, 60))

    transaction = {
        # Core transaction
        "transactionId": f"TXN{int(time.time()*1000)}",
        "timestamp": dt.isoformat(),
        "type": tx_type,
        "amount": amount,
        "oldbalanceOrg": old_balance_org,
        "newbalanceOrig": new_balance_org,
        "nameOrig": fake.name(),
        "nameDest": fake.company() if tx_type == 'PAYMENT' else fake.name(),
        
        # Transaction Patterns
        "round_amount_flag": round_amount_flag,
        "amount_just_below_threshold": amount_just_below_threshold,
        
        # Account Behavior
        "account_age_days": account_age_days,
        "is_new_account": is_new_account,
        "avg_txn_amount": avg_txn_amount,
        "txn_frequency_deviation": round(txn_frequency_deviation, 2),
        "balance_utilization": round(balance_utilization, 2),
        
        # Device & Session
        "is_new_device": is_new_device,
        "device_switch_count": device_switch_count,
        "is_emulator": is_emulator,
        "session_duration_anomaly": session_duration_anomaly,
        "multiple_sessions": multiple_sessions,
        
        # Network & Location
        "ip_country_mismatch": ip_country_mismatch,
        "vpn_detected": vpn_detected,
        "proxy_used": proxy_used,
        "location_change_rate": round(location_change_rate, 2),
        "unusual_location": unusual_location,
        "is_international": is_international,
        "high_risk_country": high_risk_country,
        "location": location,
        
        # Time
        "hour": hour,
        "day_of_week": day_of_week,
        "unusual_hour_flag": unusual_hour_flag,
        "time_since_last_txn": round(time_since_last_txn, 2),
        "rapid_txn_flag": rapid_txn_flag,
        
        # Authentication
        "otp_request_count": otp_request_count,
        "otp_bypass_attempt": otp_bypass_attempt,
        "failed_auth_count": failed_auth_count,
        "biometric_failed": biometric_failed,
        "security_question_failed": security_question_failed,
        
        # Recipient
        "is_new_recipient": is_new_recipient,
        "recipient_blacklisted": recipient_blacklisted,
        "recipient_txn_count": recipient_txn_count,
        "same_recipient_rapid_txn": same_recipient_rapid_txn,
        "is_business_account": is_business_account,
        "high_risk_merchant": high_risk_merchant,
        
        # Social Engineering
        "gift_card_request": gift_card_request,
        "wire_to_new_account": wire_to_new_account,
        "urgency_keywords_detected": urgency_keywords_detected,
        "shared_link_clicked": shared_link_clicked,
        "third_party_involved": third_party_involved,
        "phone_call_mentioned": phone_call_mentioned,
        
        # Amount Patterns
        "balance_to_amount_ratio": round(balance_to_amount_ratio, 2),
        "amount_vs_avg_deviation": round(amount_vs_avg_deviation, 2),
        "unusually_small_txn": unusually_small_txn,
        "consecutive_increasing_amounts": consecutive_increasing_amounts,
        
        # Risk Scores
        "velocity_risk": velocity_risk,
        "overall_risk_score": round(overall_risk_score, 2),
    }
    
    return transaction

def start_stream(delay=1):
    """Streams realistic transactions to Kafka."""
    print("Starting transaction stream with behavioral fraud indicators...")
    print("\nFraud Detection Features:")
    print("  [AUTH] OTP bypass, biometric failed, failed auth attempts")
    print("  [DEVICE] New device, emulator, device switching")
    print("  [NETWORK] VPN, proxy, IP mismatch, high-risk country")
    print("  [TIME] Unusual hours, rapid transactions")
    print("  [SOCIAL] Gift card request, urgency, shared link, third party")
    print("  [RECIPIENT] New recipient, blacklisted, wire transfer")
    print()
    
    try:
        while True:
            txn = sanitize(generate_transaction())
            producer.send(TOPIC_NAME, txn)
            
            risk_indicators = []
            if txn['otp_bypass_attempt']: risk_indicators.append("OTP-BYPASS")
            if txn['vpn_detected']: risk_indicators.append("VPN")
            if txn['is_new_account']: risk_indicators.append("NEW-ACCT")
            if txn['gift_card_request']: risk_indicators.append("GIFT-CARD")
            if txn['urgency_keywords_detected']: risk_indicators.append("URGENT")
            if txn['is_new_recipient']: risk_indicators.append("NEW-RCPT")
            
            risk_str = " | ".join(risk_indicators) if risk_indicators else "Normal"
            print(f"Sent: {txn['transactionId']} | {txn['type']} | ${txn['amount']:,.0f} | {risk_str}")
            
            time.sleep(delay)
    except KeyboardInterrupt:
        print("Stopping stream...")
        producer.close()

if __name__ == "__main__":
    start_stream()
