FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV KAFKA_BROKER=kafka:29092

# Default command (will be overridden in docker-compose.yml)
CMD ["python"]
