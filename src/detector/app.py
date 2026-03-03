import json
import joblib
import os
from kafka import KafkaConsumer, KafkaProducer
import numpy as np

# Load Model
MODEL_PATH = 'src/model/fraud_model.pkl'

if not os.path.exists(MODEL_PATH):
    print(f"Error: Model not found at {MODEL_PATH}. Please run src/model/train.py first.")
    exit(1)

print("Loading model...")
clf = joblib.load(MODEL_PATH)

# Initialize Kafka Consumer
consumer = KafkaConsumer(
    'transactions',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='latest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Initialize Kafka Producer for Alerts
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("Fraud Detector Service Started. Waiting for transactions...")

for message in consumer:
    txn = message.value
    
    # Prepare features for prediction
    # 'type', 'amount', 'oldbalanceOrg', 'newbalanceOrig'
    
    # Map type to int (must match training mapping)
    type_map = {'PAYMENT': 0, 'TRANSFER': 1, 'CASH_OUT': 2, 'DEBIT': 3, 'CASH_IN': 4}
    
    if txn['type'] not in type_map:
        continue # Ignore unknown types or handle gracefully
        
    features = np.array([[
        type_map[txn['type']],
        txn['amount'],
        txn['oldbalanceOrg'],
        txn['newbalanceOrig']
    ]])
    
    # Predict
    prediction = clf.predict(features)[0]
    prob = clf.predict_proba(features)[0][1]
    
    status = "SAFE"
    if prediction == 1:
        status = "FRAUD"
        print(f"[ALERT] Fraud Detected! Txn: {txn['transactionId']} | Score: {prob:.2f}")
        
        # Send Alert
        alert = {
            'transactionId': txn['transactionId'],
            'status': 'BLOCKED',
            'reason': 'High Fraud Probability',
            'score': prob,
            'original_txn': txn
        }
        producer.send('fraud_alerts', alert)
    else:
        print(f"[SAFE] Txn: {txn['transactionId']} | Score: {prob:.2f}")
        # Optionally forward safe transactions to a 'processed_payments' topic
