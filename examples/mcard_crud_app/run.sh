#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install mcard module in editable mode
pip install -e ../..

# Set environment variables
export FLASK_APP=app.py
export FLASK_DEBUG=True
export FLASK_SECRET_KEY=dev
export CSRF_SECRET_KEY=dev
export MCARD_DB_PATH="$(pwd)/data/db/MCardStore.db"
export MCARD_DB_MAX_CONNECTIONS=5
export MCARD_DB_TIMEOUT=5.0
export MCARD_MAX_CONTENT_SIZE=10485760
export LOG_LEVEL=DEBUG

# Create necessary directories
mkdir -p data/db

# Run the application
python3 app.py
