import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

# ----------------------------
# 1️⃣ LOAD DATA
# ----------------------------

data = pd.read_csv("fraud_data.csv")

# ----------------------------
# 2️⃣ CLEAN COLUMN NAMES
# ----------------------------

data.columns = data.columns.str.strip()

print("Initial Shape:", data.shape)
print("\nData Types Before Cleaning:\n", data.dtypes)

# ----------------------------
# 3️⃣ REMOVE ID COLUMNS
# ----------------------------

# Common ID columns in fraud datasets
id_columns = ["nameOrig", "nameDest", "transactionId"]

for col in id_columns:
    if col in data.columns:
        data.drop(col, axis=1, inplace=True)

# ----------------------------
# 4️⃣ HANDLE MISSING VALUES
# ----------------------------

# Fill numeric columns with median
data.fillna(data.median(numeric_only=True), inplace=True)

# Fill categorical columns with "Unknown"
data.fillna("Unknown", inplace=True)

# ----------------------------
# 5️⃣ FEATURE ENGINEERING (VERY IMPORTANT)
# ----------------------------

# If these columns exist, create balance difference features
if "oldbalanceOrg" in data.columns and "newbalanceOrig" in data.columns:
    data["balance_diff_org"] = data["oldbalanceOrg"] - data["newbalanceOrig"]

if "oldbalanceDest" in data.columns and "newbalanceDest" in data.columns:
    data["balance_diff_dest"] = data["newbalanceDest"] - data["oldbalanceDest"]

# ----------------------------
# 6️⃣ ENCODE CATEGORICAL COLUMNS
# ----------------------------

categorical_cols = data.select_dtypes(include=["object"]).columns

if len(categorical_cols) > 0:
    data = pd.get_dummies(data, columns=categorical_cols, drop_first=True)

# ----------------------------
# 7️⃣ DEFINE TARGET COLUMN
# ----------------------------

# Change this if your dataset uses different target name
target_column = "fraud_label"

if target_column not in data.columns:
    print("Available columns:", data.columns)
    raise ValueError("Target column not found. Update target_column name.")

X = data.drop(target_column, axis=1)
y = data[target_column]

print("\nAfter Preprocessing Shape:", X.shape)
print("\nObject columns left:", X.select_dtypes(include=["object"]).columns)

# ----------------------------
# 8️⃣ HANDLE IMBALANCE (OPTIONAL BUT RECOMMENDED)
# ----------------------------

print("\nClass Distribution Before SMOTE:\n", y.value_counts())

smote = SMOTE(random_state=42)
X, y = smote.fit_resample(X, y)

print("\nClass Distribution After SMOTE:\n", pd.Series(y).value_counts())

# ----------------------------
# 9️⃣ TRAIN-TEST SPLIT
# ----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# ----------------------------
# 🔟 FEATURE SCALING (Optional for RF, Required for LR/NN)
# ----------------------------

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

print("\nFinal Train Shape:", X_train.shape)
print("Final Test Shape:", X_test.shape)

print("\nPreprocessing Completed Successfully ✅")
