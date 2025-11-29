#!/bin/bash

# Find the PID from the file
if [ -f "server.pid" ]; then
    PID=$(cat server.pid)
    echo "Found server PID: $PID"

    # Check if the process is still running
    if ps -p $PID > /dev/null; then
        echo "Stopping server..."
        kill $PID
        fuser -k 8001/tcp
        echo "Server stopped."
    else
        echo "Server process not found. It might have already been stopped."
    fi

    # Remove the PID file
    rm server.pid
else
    echo "server.pid file not found. Is the server running?"
fi
