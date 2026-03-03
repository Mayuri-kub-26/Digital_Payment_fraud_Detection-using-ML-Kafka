# Real-Time Payment Fraud Detection

## Setup

1.  **Start Kafka Infrastructure**
    Make sure Docker Desktop is running.
    ```bash
    docker-compose up -d
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the System**
    You will need 3 separate terminals:

    *   **Terminal 1 (Streamlit Dashboard)**:
        ```bash
        streamlit run src/dashboard/app.py
        ```
    *   **Terminal 2 (Fraud Detector)**:
        ```bash
        python src/detector/app.py
        ```
    *   **Terminal 3 (Transaction Producer)**:
        (This is triggered via the Dashboard, but can run standalone)
        ```bash
        python src/producer/app.py
        ```

## Architecture
- **Kafka**: Message broker for transactions.
- **Producer**: Simulates payment traffic.
- **Detector**: Consumes transactions and checks against ML model.
- **Dashboard**: Visualizes the flow.
