#!/bin/bash

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Start the Uvicorn server in the background
echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Get the process ID (PID) of the background process
PID=$!

# Save the PID to a file so we can stop it later
echo $PID > server.pid

echo "Server started with PID $PID."
echo "Access the application at http://127.0.0.1:8000"
