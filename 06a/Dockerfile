# STAGE 1: Builder
FROM public.ecr.aws/docker/library/python:3.11-slim AS builder
WORKDIR /app

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# STAGE 2: Runtime
FROM public.ecr.aws/docker/library/python:3.11-slim AS runtime
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . /app/
RUN chown -R appuser:appuser /app && chmod +x /app/start.sh

USER appuser

ENV PYTHONPATH=/app
ENV PORT=8000
ENV STREAMLIT_PORT=8501

EXPOSE $PORT
EXPOSE $STREAMLIT_PORT

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('FASTAPI_PORT', '8000') + '/health')" || exit 1

CMD ["/app/start.sh"]
