from celery import shared_task
from trading_bot.data.ingestion import DataIngestion
from trading_bot.exchange_adapters.binance import BinanceAdapter
from trading_bot.exchange_adapters.alpaca import AlpacaAdapter
import os

SYMBOLS_CRYPTO = os.getenv("SYMBOLS_CRYPTO", "BTC/USDT,ETH/USDT").split(",")
SYMBOLS_STOCKS = os.getenv("SYMBOLS_STOCKS", "AAPL,MSFT").split(",")

@shared_task
def ingest_candles():
    print("[Celery] Ingesting crypto candles...")
    crypto = DataIngestion(BinanceAdapter(), exchange_name="binance")
    crypto.fetch_and_store_candles(SYMBOLS_CRYPTO)

    print("[Celery] Ingesting stock candles...")
    stock = DataIngestion(AlpacaAdapter(), exchange_name="alpaca")
    stock.fetch_and_store_candles(SYMBOLS_STOCKS)

@shared_task
def ingest_ticker():
    print("[Celery] Ingesting crypto ticker...")
    crypto = DataIngestion(BinanceAdapter(), exchange_name="binance")
    crypto.fetch_and_store_ticker(SYMBOLS_CRYPTO)

    print("[Celery] Ingesting stock ticker...")
    stock = DataIngestion(AlpacaAdapter(), exchange_name="alpaca")
    stock.fetch_and_store_ticker(SYMBOLS_STOCKS)

@shared_task
def ingest_orderbook():
    print("[Celery] Ingesting crypto orderbook...")
    crypto = DataIngestion(BinanceAdapter(), exchange_name="binance")
    crypto.fetch_and_store_orderbook(SYMBOLS_CRYPTO)

    print("[Celery] Ingesting stock orderbook...")
    stock = DataIngestion(AlpacaAdapter(), exchange_name="alpaca")
    stock.fetch_and_store_orderbook(SYMBOLS_STOCKS)
