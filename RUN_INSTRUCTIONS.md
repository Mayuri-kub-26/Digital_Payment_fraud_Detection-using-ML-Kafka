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

## Running the System

You no longer need multiple terminals! Follow these steps:

1.  **Start Everything**
    Open a terminal in the project root and run:
    ```powershell
    docker-compose up --build
    ```
    *Note: The first time will take a few minutes to build the images.*

2.  **Monitor the Dashboard**
    Open [http://localhost:8501](http://localhost:8501) in your browser.

3.  **View Logs (Optional)**
    If you want to see what's happening behind the scenes (like the old terminal outputs):
    ```powershell
    docker-compose logs -f
    ```


## Troubleshooting
- If you see a "Model not found" error, run:
  ```powershell
  python src/model/train.py
  ```
