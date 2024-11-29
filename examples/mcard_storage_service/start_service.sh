#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default values if not in environment
HOST=${MCARD_SERVICE_HOST:-0.0.0.0}
PORT=${MCARD_SERVICE_PORT:-8000}
WORKERS=${MCARD_SERVICE_WORKERS:-4}
LOG_LEVEL=${MCARD_SERVICE_LOG_LEVEL:-info}

echo "Starting MCard Storage Service..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Workers: $WORKERS"
echo "Log Level: $LOG_LEVEL"

# Start the service using uvicorn
uvicorn mcard_storage_service:app \
    --host $HOST \
    --port $PORT \
    --workers $WORKERS \
    --log-level $LOG_LEVEL
