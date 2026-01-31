# Stage 1: Builder stage
FROM python:3.11-alpine AS builder

RUN apk add --no-cache gcc musl-dev postgresql-dev

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-alpine

RUN apk add --no-cache libpq && rm -rf /var/cache/apk/*

RUN addgroup -g 1000 jhonapp && \
    adduser -D -u 1000 -G jhonapp jhonapp

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=jhonapp:jhonapp src/ .

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

USER jhonapp

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c \"import requests; requests.get('http://localhost:5000/health')\" || exit 1

# CMD sin comillas JSON
CMD python app.py
