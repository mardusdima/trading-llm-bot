FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev gcc && \
    apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY trading_bot ./trading_bot

# Entrypoint defaults to uvicorn app, override for worker
CMD ["uvicorn", "trading_bot.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
