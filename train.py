import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

# ----------------------------
# 1. Load Your Dataset
# ----------------------------

# Change this to your dataset path
data = pd.read_csv("C:\Users\mmayu\Downloads\Documents\Desktop\Final_year_Project\fraud_data.csv")

# Example: assuming 'fraud_label' is target column
X = data.drop("fraud_label", axis=1)
y = data["fraud_label"]

# ----------------------------
# 2. Train Test Split
# ----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ----------------------------
# 3. Set MLflow Experiment
# ----------------------------

mlflow.set_experiment("Digital_Payment_Fraud_Detection")

with mlflow.start_run():

    # ----------------------------
    # 4. Model Hyperparameters
    # ----------------------------
    
    n_estimators = 200
    max_depth = 10
    random_state = 42

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1
    )

    # Log Parameters
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)
    mlflow.log_param("random_state", random_state)

    # ----------------------------
    # 5. Train Model
    # ----------------------------

    model.fit(X_train, y_train)

    # ----------------------------
    # 6. Predictions
    # ----------------------------

    y_pred = model.predict(X_test)

    # ----------------------------
    # 7. Evaluation Metrics
    # ----------------------------

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    # Log Metrics
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)
    mlflow.log_metric("f1_score", f1)

    print("Accuracy:", accuracy)
    print("Precision:", precision)
    print("Recall:", recall)
    print("F1 Score:", f1)

    # ----------------------------
    # 8. Confusion Matrix
    # ----------------------------

    cm = confusion_matrix(y_test, y_pred)

    plt.figure(figsize=(6,4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")

    plt.savefig("confusion_matrix.png")
    mlflow.log_artifact("confusion_matrix.png")

    # ----------------------------
    # 9. Log Model
    # ----------------------------

    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="fraud_model",
        registered_model_name="Fraud_Detection_Model"
    )

print("Training completed & logged in MLflow!")
