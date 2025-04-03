#!/bin/bash

# Script to start the Parking Management FastAPI application

echo "Starting Parking Management System..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Change to the script's directory (assuming this script is in the project root)
cd "$SCRIPT_DIR"

# --- MODIFIED: Activate the Python virtual environment using the provided absolute path ---
VENV_PATH="/Users/ayush/Documents/GitHub/parking-management/.venv/bin/activate"

if [ -f "$VENV_PATH" ]; then
  echo "Activating virtual environment from: $VENV_PATH"
  source "$VENV_PATH"
else
  echo "Virtual environment activation script not found at: $VENV_PATH"
  echo "Attempting to run with system Python. Dependencies might be missing."
fi
# --- END MODIFICATION ---

# Run the Uvicorn server
# Using host 127.0.0.1 (localhost only) and port 8000
echo "Launching server on http://127.0.0.1:8000 (Press CTRL+C to stop)"
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Optional: Keep the terminal window open after server stops
echo "-----------------------------------------------------"
echo "Server stopped. Press Enter key to close this window."
read -p "" # Waits for user to press Enter