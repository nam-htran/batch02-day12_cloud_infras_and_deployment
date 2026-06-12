#!/bin/bash

export FASTAPI_PORT=${FASTAPI_PORT:-8000}
export PORT=${PORT:-8501}

# Khởi động FastAPI Backend ngầm
echo "Starting FastAPI on port $FASTAPI_PORT..."
uvicorn app.main:app --host 0.0.0.0 --port $FASTAPI_PORT &

# Khởi động Streamlit Web UI (cho User) sử dụng cổng public của Railway
echo "Starting Streamlit on port $PORT..."
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
