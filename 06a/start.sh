#!/bin/bash

export PORT=${PORT:-8000}
export STREAMLIT_PORT=${STREAMLIT_PORT:-8501}

# Khởi động FastAPI Backend ngầm (để pass Healthcheck và API test)
echo "Starting FastAPI on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT &

# Khởi động Streamlit Web UI (cho User)
echo "Starting Streamlit on port $STREAMLIT_PORT..."
streamlit run app.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0
