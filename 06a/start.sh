#!/bin/bash
echo "Starting A2A Backend Servers inside single Docker container..."

# Chạy các Worker Agents ngầm
python a2a_system/legal_rag_agent.py &
python a2a_system/web_search_agent.py &
python a2a_system/synthesizer_agent.py &
sleep 2

# Chạy Supervisor Agent ngầm
python a2a_system/supervisor_agent.py &
sleep 2

echo "Starting Streamlit UI..."
# Lấy PORT do Railway cấp, nếu không có thì lấy 8501
PORT=${PORT:-8501}
streamlit run group_project/app.py --server.port $PORT --server.address 0.0.0.0
