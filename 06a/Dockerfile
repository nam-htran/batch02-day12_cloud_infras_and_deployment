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

# Copy system packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . /app/

RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app

# Default command (will be overridden by docker-compose)
CMD ["python", "--version"]
