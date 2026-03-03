# How to Run the Real-Time Payment Fraud Detection System

Follow these steps to set up and run the application.

## Prerequisites
- **Docker Desktop**: Must be installed and running.
- **Python**: Version 3.8+ installed.

## Step 1: Start Infrastructure
Open a terminal in the project root (`Final_year_Project`) and run:
```powershell
docker-compose up -d
```
*Wait ~1 minute for Kafka/Zookeeper to initialize.*

## Step 2: Environment Setup
1. Create a virtual environment:
   ```powershell
   python -m venv venv
   ```
2. Activate it:
   ```powershell
   .\venv\Scripts\Activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Step 3: Run Components
You need **3 separate terminals**.

**Terminal 1: Dashboard**
```powershell
.\venv\Scripts\Activate
streamlit run src/dashboard/app.py
```

**Terminal 2: Fraud Detector**
```powershell
.\venv\Scripts\Activate
python src/detector/app.py
```

**Terminal 3: Transaction Producer**
(Or click "Start Simulation" in the Dashboard)
```powershell
.\venv\Scripts\Activate
python src/producer/app.py
```

## Troubleshooting
- If you see a "Model not found" error, run:
  ```powershell
  python src/model/train.py
  ```
