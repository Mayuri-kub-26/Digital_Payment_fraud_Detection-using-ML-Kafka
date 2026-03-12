import os
import json
import time
import random
from kafka import KafkaProducer
import numpy as np
from datetime import datetime
from faker import Faker

fake = Faker()

# Initialize Kafka Producer with Retries
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')

def get_producer():
    import time
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

def generate_transaction():
    """
    Generates a single random transaction.
    """
    tx_type = np.random.choice(['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT', 'CASH_IN'])
    amount = round(np.random.uniform(10, 50000), 2)
    old_balance_org = round(np.random.uniform(500, 100000), 2)
    
    # Logic to update balance
    new_balance_org = old_balance_org - amount if tx_type in ['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT'] else old_balance_org + amount
    new_balance_org = max(0, new_balance_org)

    transaction = {
        "transactionId": f"TXN{int(time.time()*1000)}",
        "timestamp": datetime.now().isoformat(),
        "type": tx_type,
        "amount": amount,
        "oldbalanceOrg": old_balance_org,
        "newbalanceOrig": new_balance_org,
        "nameOrig": fake.name(),
        "nameDest": fake.company() if tx_type == 'PAYMENT' else fake.name(),
    }
    return transaction

def start_stream(delay=1):
    """
    Starts streaming transactions to Kafka.
    """
    print(f"Starting transaction stream to topic '{TOPIC_NAME}'...")
    try:
        while True:
            txn = generate_transaction()
            producer.send(TOPIC_NAME, txn)
            print(f"Sent: {txn['transactionId']} | {txn['type']} | ${txn['amount']}")
            time.sleep(delay)
    except KeyboardInterrupt:
        print("Stopping stream...")
        producer.close()

if __name__ == "__main__":
    start_stream()
