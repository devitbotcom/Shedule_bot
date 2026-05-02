FROM python:3.11.14-slim

WORKDIR /app

# Install supercronic (Docker-native cron daemon, non-root, SIGTERM-clean)
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates tzdata \
    && curl -fsSL https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64 \
       -o /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
