import pandas as pd
import numpy as np
from faker import Faker
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import os

# Initialize Faker
fake = Faker()
np.random.seed(42)

# ── Feature columns (comprehensive behavioral fraud detection) ─────────────────
FEATURE_COLS = [
    # Transaction Features
    'type', 'amount', 'oldbalanceOrg', 'newbalanceOrig',
    'balanceDiff', 'highAmountFlag', 'round_amount_flag',
    'amount_just_below_threshold',
    
    # Account Behavior Features
    'account_age_days', 'is_new_account', 'avg_txn_amount',
    'txn_frequency_deviation', 'balance_utilization',
    
    # Device & Session Features
    'is_new_device', 'device_switch_count', 'is_emulator',
    'session_duration_anomaly', 'multiple_sessions',
    
    # Network & Location Features
    'ip_country_mismatch', 'vpn_detected', 'proxy_used',
    'location_change_rate', 'unusual_location',
    'is_international', 'high_risk_country',
    
    # Time-based Features
    'hour', 'day_of_week', 'unusual_hour_flag',
    'time_since_last_txn', 'rapid_txn_flag',
    
    # Authentication & Verification Features
    'otp_request_count', 'otp_bypass_attempt', 'failed_auth_count',
    'biometric_failed', 'security_question_failed',
    
    # Recipient & Beneficiary Features
    'is_new_recipient', 'recipient_blacklisted',
    'recipient_txn_count', 'same_recipient_rapid_txn',
    'is_business_account', 'high_risk_merchant',
    
    # Social Engineering Indicators
    'gift_card_request', 'wire_to_new_account',
    'urgency_keywords_detected', 'shared_link_clicked',
    'third_party_involved', 'phone_call_mentioned',
    
    # Amount & Value Patterns
    'balance_to_amount_ratio', 'amount_vs_avg_deviation',
    'unusually_small_txn', 'consecutive_increasing_amounts',
    
    # Risk Scoring
    'velocity_risk', 'overall_risk_score'
]

def generate_synthetic_data(num_records=15000):
    """
    Generates realistic transaction data with COMPREHENSIVE fraud patterns.
    Based on real fraud research from IEEE, Nature, and academic papers.
    """
    print(f"Generating {num_records} transaction records with research-based fraud patterns...")

    data = []
    type_map = {'PAYMENT': 0, 'TRANSFER': 1, 'CASH_OUT': 2, 'DEBIT': 3, 'CASH_IN': 4}
    
    # High-risk countries known for fraud
    HIGH_RISK_COUNTRIES = ['Nigeria', 'Ghana', 'Kenya', 'Pakistan', 'Bangladesh']
    
    # Scam-prone locations
    SCAM_LOCATIONS = ['Delhi', 'Mumbai', 'Kolkata']
    
    # Unusual hours (fraudsters active)
    HIGH_RISK_HOURS = list(range(0, 6))
    
    # Gift card merchants (common scam)
    GIFT_CARD_MERCHANTS = ['Amazon', 'Google Play', 'Apple', 'Steam', 'Microsoft']

    for i in range(num_records):
        # ── SCENARIO TYPE: Normal vs Fraud ──
        # 85% normal users, 15% fraudsters (realistic ratio)
        is_fraudster = np.random.random() < 0.15
        
        # ── ACCOUNT AGE ──
        if is_fraudster:
            # Fraudsters often use NEW accounts (< 30 days)
            account_age_days = np.random.randint(1, 60)
        else:
            # Normal users have established accounts
            account_age_days = np.random.randint(30, 2000)
        is_new_account = 1 if account_age_days < 30 else 0
        
        # ── TRANSACTION TYPE ──
        if is_fraudster:
            # Fraudsters prefer TRANSFER and CASH_OUT (to move money out)
            tx_type = np.random.choice(['TRANSFER', 'CASH_OUT', 'PAYMENT'], p=[0.5, 0.3, 0.2])
        else:
            tx_type = np.random.choice(['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT', 'CASH_IN'])
        
        # ── AMOUNT PATTERNS ──
        # Fraudsters often use ROUND amounts or just below thresholds
        if is_fraudster and np.random.random() < 0.25:
            # Round amounts like 1000, 5000, 10000
            amount = round(np.random.choice([1000, 2000, 5000, 10000, 15000, 20000, 49900]), 2)
        elif is_fraudster and np.random.random() < 0.2:
            # Just below threshold ($4999, $9999, $19999)
            amount = round(np.random.choice([4999, 9999, 19999, 24999, 29999, 49999]), 2)
        else:
            amount = round(np.random.uniform(10, 50000), 2)
        
        round_amount_flag = 1 if amount % 1000 == 0 else 0
        amount_just_below_threshold = 1 if amount in [4999, 9999, 19999, 24999, 29999, 49999] else 0
        
        # ── BALANCE PATTERNS ──
        if is_new_account:
            # New accounts often have suspicious round starting balances
            old_balance_org = round(np.random.choice([5000, 10000, 20000, 50000]), 2)
        else:
            old_balance_org = round(np.random.uniform(500, 100000), 2)
        
        # Fraudsters DRAIN accounts completely
        if is_fraudster and tx_type in ['CASH_OUT', 'TRANSFER']:
            if np.random.random() < 0.85:  # 85% drain completely
                new_balance_org = 0
            else:
                new_balance_org = max(0, old_balance_org - amount)
        else:
            new_balance_org = max(0, old_balance_org - amount)
        
        # ── AVERAGE TRANSACTION AMOUNT ──
        avg_txn_amount = round(np.random.uniform(500, 50000), 2)
        amount_vs_avg_deviation = abs(amount - avg_txn_amount) / avg_txn_amount if avg_txn_amount > 0 else 0
        
        # ── TRANSACTION FREQUENCY ──
        if is_fraudster:
            # Fraudsters have IRREGULAR frequency
            txn_frequency_deviation = np.random.uniform(2.0, 5.0)
        else:
            txn_frequency_deviation = np.random.uniform(0.1, 1.5)
        
        # ── BALANCE UTILIZATION ──
        balance_utilization = amount / old_balance_org if old_balance_org > 0 else 1
        
        # ── DEVICE FEATURES ──
        if is_fraudster:
            # Fraudsters often use NEW/EMULATED devices
            is_new_device = np.random.choice([0, 1], p=[0.3, 0.7])
            is_emulator = np.random.choice([0, 1], p=[0.4, 0.6])
            device_switch_count = np.random.randint(0, 5)
        else:
            is_new_device = np.random.choice([0, 1], p=[0.8, 0.2])
            is_emulator = 0
            device_switch_count = np.random.randint(0, 2)
        
        # ── SESSION PATTERNS ──
        if is_fraudster:
            # Suspiciously SHORT sessions (quick fraud)
            session_duration_anomaly = np.random.choice([0, 1], p=[0.2, 0.8])
            multiple_sessions = np.random.choice([0, 1], p=[0.3, 0.7])
        else:
            session_duration_anomaly = np.random.choice([0, 1], p=[0.9, 0.1])
            multiple_sessions = np.random.choice([0, 1], p=[0.95, 0.05])
        
        # ── NETWORK FEATURES ──
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
        
        # ── LOCATION FEATURES ──
        location = np.random.choice(['Hyderabad', 'Bangalore', 'Chennai', 'Delhi', 'Mumbai', 'Kolkata'])
        unusual_location = 1 if location in SCAM_LOCATIONS else 0
        location_change_rate = np.random.uniform(0, 1)
        if is_fraudster:
            location_change_rate = np.random.uniform(0.5, 1.0)
        
        is_international = np.random.choice([0, 0, 0, 1])  # 25% international
        
        # ── TIME FEATURES ──
        if is_fraudster:
            hour = np.random.choice([0, 1, 2, 3, 4, 5, 23], p=[0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.1])
        else:
            hour = np.random.randint(6, 23)
        
        day_of_week = np.random.randint(0, 7)
        unusual_hour_flag = 1 if hour in HIGH_RISK_HOURS else 0
        
        # Time since last transaction
        if is_fraudster:
            time_since_last_txn = np.random.uniform(0, 60)  # Quick successive
        else:
            time_since_last_txn = np.random.uniform(60, 86400)  # Normal gap
        
        rapid_txn_flag = 1 if time_since_last_txn < 60 else 0
        
        # ── AUTHENTICATION FEATURES ──
        if is_fraudster:
            # Scammers often have OTP issues (trying wrong accounts)
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
        
        # ── RECIPIENT FEATURES ──
        if is_fraudster:
            is_new_recipient = np.random.choice([0, 1], p=[0.1, 0.9])  # New recipients
            recipient_blacklisted = np.random.choice([0, 1], p=[0.4, 0.6])
        else:
            is_new_recipient = np.random.choice([0, 1], p=[0.7, 0.3])
            recipient_blacklisted = np.random.choice([0, 1], p=[0.99, 0.01])
        
        recipient_txn_count = np.random.randint(1, 50)
        same_recipient_rapid_txn = 1 if rapid_txn_flag and is_new_recipient else 0
        
        # Merchant type
        merchant = fake.company()
        is_business_account = np.random.choice([0, 1])
        high_risk_merchant = 1 if any(gc in merchant for gc in GIFT_CARD_MERCHANTS) else 0
        
        # ── SOCIAL ENGINEERING INDICATORS ──
        if is_fraudster:
            # Common scam patterns
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
        
        # ── AMOUNT PATTERNS ──
        balance_to_amount_ratio = old_balance_org / amount if amount > 0 else 10
        unusually_small_txn = 1 if amount < 100 and is_fraudster else 0
        consecutive_increasing_amounts = np.random.randint(0, 2)
        if is_fraudster:
            consecutive_increasing_amounts = np.random.choice([0, 1], p=[0.3, 0.7])
        
        # ── VELOCITY RISK SCORE ──
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
        
        # ── OVERALL RISK SCORE ──
        overall_risk_score = 0
        risk_factors = [
            is_new_account, is_new_device, vpn_detected, proxy_used,
            unusual_hour_flag, is_new_recipient, gift_card_request,
            otp_bypass_attempt, biometric_failed, high_risk_country,
            recipient_blacklisted, urgency_keywords_detected,
            round_amount_flag, session_duration_anomaly
        ]
        overall_risk_score = sum(risk_factors) / len(risk_factors)
        
        # ── FRAUD LABELING (Comprehensive Rules) ──
        is_fraud = 0
        
        # Rule 1: Social Engineering Patterns (HIGH PRIORITY)
        if gift_card_request and amount > 1000:
            if np.random.random() < 0.85: is_fraud = 1
        
        # Rule 2: OTP Bypass + New Account + High Amount (Account Takeover)
        if otp_bypass_attempt and is_new_account and amount > 5000:
            if np.random.random() < 0.80: is_fraud = 1
        
        # Rule 3: VPN + Proxy + International + High Amount (Money Laundering)
        if vpn_detected and proxy_used and is_international and amount > 10000:
            if np.random.random() < 0.82: is_fraud = 1
        
        # Rule 4: New Account + Urgent + New Recipient (Classic Scam)
        if is_new_account and urgency_keywords_detected and is_new_recipient and amount > 2000:
            if np.random.random() < 0.78: is_fraud = 1
        
        # Rule 5: Wire Transfer to New Account + Gift Card Pattern
        if tx_type == 'TRANSFER' and is_new_recipient and gift_card_request:
            if np.random.random() < 0.75: is_fraud = 1
        
        # Rule 6: Rapid Transactions + Multiple Failed Auth
        if rapid_txn_flag and failed_auth_count >= 2:
            if np.random.random() < 0.72: is_fraud = 1
        
        # Rule 7: High-Risk Country + VPN + Unusual Hour
        if high_risk_country and vpn_detected and unusual_hour_flag:
            if np.random.random() < 0.70: is_fraud = 1
        
        # Rule 8: New Device + Biometric Failed + Retry
        if is_new_device and biometric_failed and otp_request_count >= 3:
            if np.random.random() < 0.68: is_fraud = 1
        
        # Rule 9: Account Draining Pattern
        if new_balance_org == 0 and old_balance_org > 10000 and amount > 5000:
            if np.random.random() < 0.65: is_fraud = 1
        
        # Rule 10: Shared Link + Wire Transfer (Phishing scam)
        if shared_link_clicked and tx_type == 'TRANSFER' and amount > 3000:
            if np.random.random() < 0.70: is_fraud = 1
        
        # Rule 11: Third Party Involved + High Amount (Authorized Push Payment Fraud)
        if third_party_involved and amount > 5000 and is_new_recipient:
            if np.random.random() < 0.72: is_fraud = 1
        
        # Rule 12: Phone Call Mentioned + Gift Card (Impersonation Scam)
        if phone_call_mentioned and gift_card_request:
            if np.random.random() < 0.80: is_fraud = 1
        
        # Rule 13: High Velocity Risk Score
        if velocity_risk >= 5:
            if np.random.random() < 0.65: is_fraud = 1
        
        # Rule 14: Recipient Blacklisted
        if recipient_blacklisted and amount > 2000:
            if np.random.random() < 0.75: is_fraud = 1
        
        # Rule 15: New Account + Large Transaction + Unusual Location
        if is_new_account and amount > 15000 and unusual_location:
            if np.random.random() < 0.60: is_fraud = 1
        
        # Rule 16: Emulator Detection + Any Transaction
        if is_emulator and amount > 1000:
            if np.random.random() < 0.60: is_fraud = 1
        
        # Rule 17: Multiple Sessions + Rapid Txn
        if multiple_sessions and rapid_txn_flag:
            if np.random.random() < 0.55: is_fraud = 1
        
        # Rule 18: Amount vs Average Deviation (unusual spending pattern)
        if amount_vs_avg_deviation > 3.0 and is_new_account:
            if np.random.random() < 0.50: is_fraud = 1
        
        # Rule 19: Consecutive Increasing Amounts (testing account limits)
        if consecutive_increasing_amounts and is_new_account:
            if np.random.random() < 0.45: is_fraud = 1
        
        # Rule 20: Session Duration Anomaly + High Amount
        if session_duration_anomaly and amount > 8000:
            if np.random.random() < 0.50: is_fraud = 1

        # ── ENGINEERED FEATURES ──
        balance_diff = old_balance_org - new_balance_org
        high_amount_flag = 1 if amount > 30000 else 0

        data.append({
            # Transaction Features
            'type': type_map[tx_type],
            'amount': amount,
            'oldbalanceOrg': old_balance_org,
            'newbalanceOrig': new_balance_org,
            'balanceDiff': balance_diff,
            'highAmountFlag': high_amount_flag,
            'round_amount_flag': round_amount_flag,
            'amount_just_below_threshold': amount_just_below_threshold,
            
            # Account Behavior
            'account_age_days': account_age_days,
            'is_new_account': is_new_account,
            'avg_txn_amount': avg_txn_amount,
            'txn_frequency_deviation': round(txn_frequency_deviation, 2),
            'balance_utilization': round(balance_utilization, 2),
            
            # Device & Session
            'is_new_device': is_new_device,
            'device_switch_count': device_switch_count,
            'is_emulator': is_emulator,
            'session_duration_anomaly': session_duration_anomaly,
            'multiple_sessions': multiple_sessions,
            
            # Network & Location
            'ip_country_mismatch': ip_country_mismatch,
            'vpn_detected': vpn_detected,
            'proxy_used': proxy_used,
            'location_change_rate': round(location_change_rate, 2),
            'unusual_location': unusual_location,
            'is_international': is_international,
            'high_risk_country': high_risk_country,
            
            # Time
            'hour': hour,
            'day_of_week': day_of_week,
            'unusual_hour_flag': unusual_hour_flag,
            'time_since_last_txn': round(time_since_last_txn, 2),
            'rapid_txn_flag': rapid_txn_flag,
            
            # Authentication
            'otp_request_count': otp_request_count,
            'otp_bypass_attempt': otp_bypass_attempt,
            'failed_auth_count': failed_auth_count,
            'biometric_failed': biometric_failed,
            'security_question_failed': security_question_failed,
            
            # Recipient
            'is_new_recipient': is_new_recipient,
            'recipient_blacklisted': recipient_blacklisted,
            'recipient_txn_count': recipient_txn_count,
            'same_recipient_rapid_txn': same_recipient_rapid_txn,
            'is_business_account': is_business_account,
            'high_risk_merchant': high_risk_merchant,
            
            # Social Engineering
            'gift_card_request': gift_card_request,
            'wire_to_new_account': wire_to_new_account,
            'urgency_keywords_detected': urgency_keywords_detected,
            'shared_link_clicked': shared_link_clicked,
            'third_party_involved': third_party_involved,
            'phone_call_mentioned': phone_call_mentioned,
            
            # Amount Patterns
            'balance_to_amount_ratio': round(balance_to_amount_ratio, 2),
            'amount_vs_avg_deviation': round(amount_vs_avg_deviation, 2),
            'unusually_small_txn': unusually_small_txn,
            'consecutive_increasing_amounts': consecutive_increasing_amounts,
            
            # Risk Scores
            'velocity_risk': velocity_risk,
            'overall_risk_score': round(overall_risk_score, 2),
            
            'isFraud': is_fraud
        })

    return pd.DataFrame(data)


def train_model():
    """Trains XGBoost with research-based fraud patterns."""
    df = generate_synthetic_data()

    X = df[FEATURE_COLS]
    y = df['isFraud']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Handle class imbalance
    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    spw = neg / pos if pos > 0 else 1

    fraud_count = df['isFraud'].sum()
    legit_count = len(df) - fraud_count
    print(f"Dataset: {len(df)} records | Legit: {legit_count} | Fraud: {fraud_count} ({fraud_count/len(df)*100:.1f}%)")
    print(f"Training XGBoost — neg:{neg}  pos:{pos}  scale_pos_weight:{spw:.1f}")

    clf = XGBClassifier(
        n_estimators=500,
        max_depth=8,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=spw,
        eval_metric='logloss',
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    print("\n" + "="*60)
    print("MODEL EVALUATION")
    print("="*60)
    print(classification_report(y_test, y_pred))
    
    auc = roc_auc_score(y_test, y_proba)
    print(f"ROC-AUC Score: {auc:.4f}")
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"  TN: {cm[0][0]:5d}  FP: {cm[0][1]:5d}")
    print(f"  FN: {cm[1][0]:5d}  TP: {cm[1][1]:5d}")

    # Feature importance
    print("\n" + "="*60)
    print("TOP 15 MOST IMPORTANT FRAUD INDICATORS")
    print("="*60)
    importance = pd.DataFrame({
        'feature': FEATURE_COLS,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for i, row in importance.head(15).iterrows():
        bar = "#" * int(row['importance'] * 50)
        print(f"  {row['feature']:35s} {row['importance']:.4f} [{bar}]")

    model_path = 'src/model/fraud_model.pkl'
    joblib.dump({'model': clf, 'features': FEATURE_COLS}, model_path)
    print(f"\nModel saved to {model_path}")


if __name__ == "__main__":
    os.makedirs('src/model', exist_ok=True)
    train_model()
