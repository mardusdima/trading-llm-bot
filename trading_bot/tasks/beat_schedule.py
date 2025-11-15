from celery.schedules import crontab

beat_schedule = {
    'ingest_candles_job': {
        'task': 'trading_bot.tasks.ingest.ingest_candles',
        'schedule': 60.0,  # every minute
    },
    'ingest_ticker_job': {
        'task': 'trading_bot.tasks.ingest.ingest_ticker',
        'schedule': 10.0,  # every 10 seconds
    },
    'ingest_orderbook_job': {
        'task': 'trading_bot.tasks.ingest.ingest_orderbook',
        'schedule': 10.0,
    },
    'trading_cycle_crypto_job': {
        'task': 'trading_bot.tasks.orders.run_trading_cycle_crypto',
        'schedule': 300.0,  # every 5 minutes
    },
    'trading_cycle_stocks_job': {
        'task': 'trading_bot.tasks.orders.run_trading_cycle_stocks',
        'schedule': 300.0,  # every 5 minutes
    },
}
