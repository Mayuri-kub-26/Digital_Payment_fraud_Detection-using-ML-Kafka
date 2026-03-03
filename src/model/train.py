import pandas as pd
import numpy as np
from faker import Faker
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

# Initialize Faker
fake = Faker()
np.random.seed(42)

def generate_synthetic_data(num_records=10000):
    """
    Generates a synthetic dataset of transactions.
    """
    print(f"Generating {num_records} transaction records...")
    
    data = []
    
    for _ in range(num_records):
        # Simulate transaction details
        amount = round(np.random.uniform(10, 50000), 2)
        old_balance_org = round(np.random.uniform(500, 100000), 2)
        new_balance_org = max(0, old_balance_org - amount)
        
        # Randomly choose transaction type
        tx_type = np.random.choice(['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT', 'CASH_IN'])
        
        # Fraud logic: Let's inject some patterns
        is_fraud = 0
        
        # Pattern 1: Large transfers with empty destination account
        if tx_type == 'TRANSFER' and amount > 20000:
            if np.random.random() < 0.3:
                is_fraud = 1
                
        # Pattern 2: Cash out all funds
        if tx_type == 'CASH_OUT' and new_balance_org == 0:
            if np.random.random() < 0.4:
                is_fraud = 1
                
        data.append({
            'type': tx_type,
            'amount': amount,
            'oldbalanceOrg': old_balance_org,
            'newbalanceOrig': new_balance_org,
            'isFraud': is_fraud
        })
        
    df = pd.DataFrame(data)
    return df

def train_model():
    """
    Trains a Random Forest Classifier to detect fraud.
    """
    df = generate_synthetic_data()
    
    # Preprocessing
    # Map transaction type to numeric
    type_map = {'PAYMENT': 0, 'TRANSFER': 1, 'CASH_OUT': 2, 'DEBIT': 3, 'CASH_IN': 4}
    df['type'] = df['type'].map(type_map)
    
    X = df[['type', 'amount', 'oldbalanceOrg', 'newbalanceOrig']]
    y = df['isFraud']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Classifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    print("\nModel Evaluation:")
    print(classification_report(y_test, y_pred))
    
    # Save the model
    model_path = 'src/model/fraud_model.pkl'
    joblib.dump(clf, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs('src/model', exist_ok=True)
    train_model()
