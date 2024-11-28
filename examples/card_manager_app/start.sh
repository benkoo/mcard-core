#!/bin/bash

# Function to check if a process is running
is_running() {
    pgrep -f "$1" > /dev/null 2>&1
}

# Start the API service if not running
if ! is_running "mcard/interfaces/api/app.py"; then
    echo "Starting API service..."
    (cd /Users/bkoo/Documents/Development/mcard-core && python3 -m mcard.interfaces.api.app) &
    sleep 2 # Give it a moment to start
fi

# Start the card manager app
echo "Starting Card Manager App..."
(cd /Users/bkoo/Documents/Development/mcard-core/examples/card_manager_app && python3 app.py)
