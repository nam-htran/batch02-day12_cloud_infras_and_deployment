#!/bin/bash
echo "Starting A2A Backend Servers (Optimized)..."

# Function to handle cleanup on exit
cleanup() {
    echo "Stopping all A2A background servers..."
    kill $(jobs -p)
    exit
}

# Register the cleanup function for when the script receives SIGINT (Ctrl+C)
trap cleanup SIGINT

# Start agents in background
uv run python a2a_system/legal_rag_agent.py &
uv run python a2a_system/web_search_agent.py &
uv run python a2a_system/synthesizer_agent.py &
sleep 2

uv run python a2a_system/supervisor_agent.py &
sleep 2

echo "A2A servers are running in the background."
echo "Press Ctrl+C to stop all servers."

# Wait for all background jobs (keeps script running until Ctrl+C)
wait
