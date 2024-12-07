#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check for .venv directory
if [ ! -d ".venv" ]; then
    echo "❌ .venv directory not found. Please make sure you are in the correct directory and the virtual environment is set up."
    exit 1
fi

# Create .env file with test configuration
echo "🔧 Creating .env file with test configuration..."
cat > .env << EOL
# Server Configuration
MCARD_API_KEY=dev_key_123
MCARD_API_PORT=5320

# Database Settings
MCARD_DB_PATH=data/mcard.db
MCARD_STORE_MAX_CONNECTIONS=5
MCARD_STORE_TIMEOUT=30.0

# Hash Configuration
MCARD_HASH_ALGORITHM=sha256
EOL

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install or upgrade required packages
echo "📦 Installing/upgrading required packages..."
pip install -U fastapi uvicorn python-dotenv mcard

# Start the server
echo "🚀 Starting MCard server..."
cd src
python server.py &
SERVER_PID=$!

# Wait for the server to be ready
echo "⏳ Waiting for server to start..."
for i in {1..30}; do
    if curl -s -H "X-API-Key: dev_key_123" http://127.0.0.1:5320/health > /dev/null; then
        echo "✅ Server is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ Server failed to start within 30 seconds"
        kill $SERVER_PID
        exit 1
    fi
    echo -n "."
done

# Keep the script running
wait $SERVER_PID
