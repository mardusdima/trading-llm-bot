# Trading LLM Bot

A modular, production-grade trading bot supporting both crypto and stock brokers (Binance, Coinbase, Alpaca, and more) with paper trading, risk management, real-time data ingestion, and strategy backtesting.

## Features
- Modular, extensible design
- Plug-and-play support for multiple broker/exchange APIs
- Real-time & historical data ingestion (Postgres/TimescaleDB)
- FastAPI REST backend with WebSocket
- Background jobs (Celery + Redis)
- Strategy engine (e.g., SMA crossover)
- Comprehensive risk management
- Portfolio tracking & P&L
- Dockerized deployment
- Environment-based configuration
- Secure credential management

## Architecture
- **API**: FastAPI (REST & WebSocket)
- **Worker**: Celery for order execution, tasks
- **DB**: PostgreSQL + TimescaleDB for timeseries ops
- **Redis**: Task queues
- **Adapters**: Unified interface for exchanges/brokers
- **Domain logic**: Strategy, risk, portfolio, execution modules

## Tech Stack
Python 3.11+, FastAPI, Celery, Redis, PostgreSQL, TimescaleDB, SQLAlchemy, Pandas, Docker, ccxt, Pydantic

## Folder Structure
```
trading-llm-bot/
├── trading_bot/
│   ├── api/            # REST & WS endpoints
│   ├── core/           # Base classes/types/errors
│   ├── config/         # Config loader
│   ├── exchange_adapters/ # Exchange/broker adapters
│   ├── data/           # Data ingestion/storage
│   ├── db/             # SQLAlchemy models
│   ├── execution/      # Order execution logic
│   ├── logging/        # Logging/audit
│   ├── portfolio/      # Portfolio & P&L
│   ├── risk/           # Risk management
│   ├── strategy/       # Strategies
│   ├── tasks/          # Celery task modules
│   └── utils/          # Helpers (rate limiting, ...)
├── tests/              # Unit/integration tests
├── docker/             # Docker-related files
├── config/             # Sample configs
├── scripts/            # Utility scripts
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── ...
```

## Configuration
- Copy `.env.sample` to `.env` and fill in required secrets/envvars.
- `ENV` selects dev, staging, or prod settings.
- API keys and DB credentials **must NOT** be stored in code!

## Usage
**Dockerized (recommended):**

```bash
docker-compose build
docker-compose up
```
- API: http://localhost:8000
- DB: localhost:5432 (see .env)
- Redis: localhost:6379

**Local:**
Install system deps (see Dockerfile), then:
```bash
pip install -r requirements.txt
uvicorn trading_bot.api.main:app --reload
```

## Testing
Run with pytest:
```bash
pytest
```

## Security Notes
- API keys/secrets via env vars only
- NEVER commit secrets
- Input validation, audit logging, and error handling require further implementation (see code TODOs)

## License
MIT (TBD)
