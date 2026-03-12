# Real-Time Payment Fraud Detection

## Setup & Running

1.  **Start the Entire System**
    Make sure Docker Desktop is running. In the project root, run:
    ```bash
    docker-compose up --build
    ```
    This single command starts:
    - **Kafka & Zookeeper** (Message Broker)
    - **Fraud Detector** (ML Prediction Service)
    - **Transaction Producer** (Traffic Simulator)
    - **Streamlit Dashboard** (Real-time UI)

2.  **Access the Dashboard**
    Open your browser and navigate to:
    [http://localhost:8501](http://localhost:8501)

3.  **Logs & Monitoring**
    To see the live processing logs (as previously shown in separate terminals):
    ```bash
    docker-compose logs -f
    ```


## Architecture
- **Kafka**: Message broker for transactions.
- **Producer**: Simulates payment traffic.
- **Detector**: Consumes transactions and checks against ML model.
- **Dashboard**: Visualizes the flow.
