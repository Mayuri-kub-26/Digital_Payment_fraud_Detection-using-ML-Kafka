# FRAUDSENSE AI - VIVA QUICK REFERENCE
## One-Page Summary for Quick Revision

---

## PROJECT BASICS
- **Name**: FraudSense AI - Real-Time Payment Fraud Detection
- **Objective**: Detect fraudulent transactions in real-time using ML
- **Tech Stack**: Python, XGBoost, Kafka, Streamlit, Docker
- **Dataset**: 15,000 synthetic transactions (47 features)

---

## ARCHITECTURE
```
Producer → Kafka → Detector → Dashboard
(Generate)  (Stream)  (ML Model) (UI)
```

---

## KEY ANSWERS

### Q: What ML algorithm did you use?
**A: XGBoost (Extreme Gradient Boosting)**
- Supervised learning algorithm
- Builds sequential decision trees
- Each tree corrects previous errors
- Best for structured/tabular data

### Q: Why XGBoost and not others?
**A:**
- Faster than Neural Networks
- More accurate than Random Forest
- Handles imbalanced data (fraud is rare)
- Provides feature importance
- Regularization prevents overfitting

### Q: How many features?
**A: 47 features** in 10 categories:
- Transaction (8)
- Account Behavior (5)
- Device & Session (5)
- Network & Location (7)
- Time-Based (5)
- Authentication (5)
- Recipient (6)
- Social Engineering (6)
- Amount Patterns (4)
- Risk Scores (2)

### Q: What is the most important feature?
**A: rapid_txn_flag (64.4%)**
- Rapid successive transactions
- Indicates automated attack or fraud script

### Q: What is model accuracy?
**A:**
- Overall Accuracy: 91%
- Fraud Detection (Recall): 93%
- ROC-AUC Score: 0.9746
- Precision: 79%

### Q: How does fraud detection work?
**A: 3 Steps:**
1. Transaction arrives with 47 features
2. XGBoost model calculates fraud probability (0-1)
3. If probability > 0.5 → Blocked as fraud

### Q: What fraud patterns are detected?
**A: 20 patterns including:**
1. Gift card request (85% fraud)
2. OTP bypass attempt (80%)
3. VPN + International transaction (82%)
4. New account + Urgency (78%)
5. Rapid transactions (65%)
6. Account draining (65%)
7. Phishing link clicked (70%)
8. Third party involved (72%)
9. Phone scam indicators (80%)
10. Blacklisted recipient (75%)

### Q: Why Kafka?
**A:**
- Handles real-time streaming
- Decouples producer and consumer
- Provides message persistence
- Supports multiple consumers

### Q: What is Streamlit?
**A:**
- Python web framework
- Creates interactive dashboards
- Used for monitoring UI

### Q: Why Docker?
**A:**
- Containerization
- Consistent environment
- Easy deployment
- All services in one place

---

## CONFUSION MATRIX (Memorize!)
```
                  Predicted
              Genuine  Fraud
Actual Genuine  1934    209    ← False Positives
Actual Fraud     63    794    ← True Positives
```
- TN = 1934 (Correctly identified genuine)
- TP = 794 (Correctly caught fraud)
- FP = 209 (Genuine wrongly blocked)
- FN = 63 (Fraud missed - danger!)

---

## METRICS FORMULA
```
Accuracy = (TP + TN) / Total = (794 + 1934) / 3000 = 91%

Recall = TP / (TP + FN) = 794 / (794 + 63) = 93%

Precision = TP / (TP + FP) = 794 / (794 + 209) = 79%
```

---

## PARAMETERS USED
```python
XGBClassifier(
    n_estimators=500,        # 500 trees
    max_depth=8,             # Max 8 levels
    learning_rate=0.03,      # Small steps
    subsample=0.8,           # 80% data per tree
    colsample_bytree=0.8,    # 80% features
    scale_pos_weight=2.5,    # Handle imbalance
    random_state=42          # Reproducible
)
```

---

## TOP 5 IMPORTANT FEATURES
| Rank | Feature | Importance |
|------|---------|------------|
| 1 | rapid_txn_flag | 64.4% |
| 2 | velocity_risk | 8.9% |
| 3 | session_duration_anomaly | 6.1% |
| 4 | newbalanceOrig | 3.5% |
| 5 | recipient_blacklisted | 2.4% |

---

## SOCIAL ENGINEERING FEATURES
| Feature | Fraud Indicator |
|---------|-----------------|
| gift_card_request | CEO scam, tech support |
| urgency_keywords | Pressure to act fast |
| shared_link_clicked | Phishing attack |
| third_party_involved | Authorized push payment |
| phone_call_mentioned | Impersonation scam |

---

## COMMON VIVA QUESTIONS

**Q: How does your system handle class imbalance?**
> Fraud is rare (15%), genuine is common (85%). We use `scale_pos_weight=2.5` to give more weight to fraud samples during training.

**Q: What is the processing time?**
> Each transaction processed in <100ms

**Q: Can it detect new fraud patterns?**
> Current model detects 20 known patterns. New patterns require retraining with updated data.

**Q: What happens to blocked transactions?**
> Alert is published to `fraud_alerts` Kafka topic and displayed on dashboard.

**Q: How is the model saved?**
> Using joblib library to pickle (serialize) the model

**Q: What is ROC-AUC 0.9746?**
> Area Under ROC Curve. Measures how well model distinguishes fraud from genuine. 0.9746 is excellent (1.0 is perfect).

---

## FILE STRUCTURE (Memorize!)
```
Final_year_Project/
├── src/
│   ├── model/
│   │   ├── train.py         # Trains XGBoost
│   │   └── fraud_model.pkl  # Trained model
│   ├── detector/
│   │   └── app.py           # Fraud detection engine
│   ├── producer/
│   │   └── app.py           # Generates transactions
│   └── dashboard/
│       ├── app.py           # Web dashboard
│       └── style.css        # Styling
├── docker-compose.yml        # Orchestration
├── Dockerfile                # Container build
├── requirements.txt          # Dependencies
└── start.bat                # Launcher
```

---

## ADVANTAGES OF THIS SYSTEM
1. Real-time detection (<100ms)
2. 93% fraud caught
3. 47 behavioral features
4. Explains why transaction flagged
5. Visual dashboard for monitoring
6. Docker for easy deployment
7. Scalable architecture

---

## LIMITATIONS
1. Uses synthetic data (not real transactions)
2. Requires retraining for new patterns
3. May have false positives (7%)
4. Single model (could use ensemble)

---

## FUTURE IMPROVEMENTS
1. Use real bank transaction data
2. Add ensemble methods (combine multiple models)
3. Implement online learning (update model continuously)
4. Add explainability features (SHAP values)
5. Integrate with actual payment gateway

---

## KEY TECHNICAL TERMS
- **XGBoost**: Gradient boosting algorithm
- **Kafka**: Message streaming broker
- **Streamlit**: Python web framework
- **Docker**: Container platform
- **Feature Engineering**: Creating meaningful features
- **Class Imbalance**: Unequal fraud/genuine ratio
- **ROC-AUC**: Model performance metric
- **False Positive**: Genuine marked as fraud
- **False Negative**: Fraud marked as genuine

---

## CODE SNIPPETS TO REMEMBER

**Feature Importance:**
```python
importance = pd.DataFrame({
    'feature': FEATURE_COLS,
    'importance': clf.feature_importances_
}).sort_values('importance', ascending=False)
```

**Prediction:**
```python
prob = clf.predict_proba(features)[0][1]
if prob > 0.5:
    print("FRAUD")
else:
    print("GENUINE")
```

**Kafka Consumer:**
```python
consumer = KafkaConsumer(
    'transactions',
    bootstrap_servers='kafka:29092',
    value_deserializer=lambda x: json.loads(x)
)
```

---

**GOOD LUCK WITH YOUR VIVA! 🎓**

---

*End of Quick Reference Card*
