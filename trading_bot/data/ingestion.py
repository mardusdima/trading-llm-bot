import os
from trading_bot.exchange_adapters.binance import BinanceAdapter
from trading_bot.exchange_adapters.alpaca import AlpacaAdapter
from trading_bot.db.models import Candle, Ticker, OrderBook
from trading_bot.db.session import get_session
from datetime import datetime

SYMBOLS_CRYPTO = os.getenv("SYMBOLS_CRYPTO", "BTC/USDT,ETH/USDT").split(",")
SYMBOLS_STOCKS = os.getenv("SYMBOLS_STOCKS", "AAPL,MSFT").split(",")

class DataIngestion:
    def __init__(self, adapter, exchange_name=None):
        self.adapter = adapter
        self.exchange_name = exchange_name or adapter.__class__.__name__.replace('Adapter','').lower()

    def fetch_and_store_candles(self, symbols, timeframe='1m'):
        for sym in symbols:
            try:
                data = self.adapter.fetch_market_data(sym, timeframe=timeframe, limit=100)
                self.save_candles(sym, data, timeframe)
                print(f"Fetched candles for {sym}: {data[:1]}")
            except Exception as e:
                print(f"Error fetching candles for {sym}: {e}")

    def fetch_and_store_ticker(self, symbols):
        for sym in symbols:
            try:
                data = self.adapter.fetch_ticker(sym)
                self.save_ticker(sym, data)
                print(f"Fetched ticker for {sym}: {data}")
            except Exception as e:
                print(f"Error fetching ticker for {sym}: {e}")

    def fetch_and_store_orderbook(self, symbols):
        for sym in symbols:
            try:
                data = self.adapter.fetch_market_data(sym, book=True)
                self.save_orderbook(sym, data)
                print(f"Fetched orderbook for {sym}: bids {data.get('bids', [])[:1]}, asks {data.get('asks', [])[:1]}")
            except Exception as e:
                print(f"Error fetching orderbook for {sym}: {e}")

    # Database persistence implementations
    def save_candles(self, symbol, data, timeframe):
        objs = []
        for entry in data:
            # ccxt: [timestamp(ms), open, high, low, close, volume]
            if isinstance(entry, dict):
                # Alpaca: dict structure
                dt = datetime.fromisoformat(entry.get('t')[:-1]) if 't' in entry else None
                objs.append(Candle(
                    exchange=self.exchange_name,
                    symbol=symbol,
                    timestamp=dt,
                    open=entry.get('o'),
                    high=entry.get('h'),
                    low=entry.get('l'),
                    close=entry.get('c'),
                    volume=entry.get('v'),
                    timeframe=timeframe
                ))
            else:
                ts = datetime.utcfromtimestamp(entry[0]/1000)
                objs.append(Candle(
                    exchange=self.exchange_name,
                    symbol=symbol,
                    timestamp=ts,
                    open=entry[1],
                    high=entry[2],
                    low=entry[3],
                    close=entry[4],
                    volume=entry[5],
                    timeframe=timeframe
                ))
        with get_session() as session:
            session.bulk_save_objects(objs)

    def save_ticker(self, symbol, data):
        exchange = self.exchange_name
        # Try to extract timestamp from data; else, use now
        ts = None
        if 'timestamp' in data:
            ts = datetime.utcfromtimestamp(data['timestamp']/1000)
        elif 'trade' in data and 't' in data['trade']:
            ts = datetime.fromisoformat(data['trade']['t'][:-1])
        else:
            ts = datetime.utcnow()
        price = data.get('close') or data.get('price') or data.get('last')
        ticker = Ticker(
            exchange=exchange,
            symbol=symbol,
            timestamp=ts,
            price=price,
            bid=data.get('bid'),
            ask=data.get('ask'),
            info=data
        )
        with get_session() as session:
            session.add(ticker)

    def save_orderbook(self, symbol, data):
        exchange = self.exchange_name
        ts = datetime.utcfromtimestamp(data['timestamp']/1000) if 'timestamp' in data and data['timestamp'] else datetime.utcnow()
        orderbook = OrderBook(
            exchange=exchange,
            symbol=symbol,
            timestamp=ts,
            bids=data.get('bids'),
            asks=data.get('asks'),
            info=data
        )
        with get_session() as session:
            session.add(orderbook)

def run_crypto_ingestion():
    binance = BinanceAdapter()
    ingest = DataIngestion(binance, exchange_name="binance")
    ingest.fetch_and_store_candles(SYMBOLS_CRYPTO)
    ingest.fetch_and_store_ticker(SYMBOLS_CRYPTO)
    ingest.fetch_and_store_orderbook(SYMBOLS_CRYPTO)

def run_stock_ingestion():
    alpaca = AlpacaAdapter()
    ingest = DataIngestion(alpaca, exchange_name="alpaca")
    ingest.fetch_and_store_candles(SYMBOLS_STOCKS)
    ingest.fetch_and_store_ticker(SYMBOLS_STOCKS)
    ingest.fetch_and_store_orderbook(SYMBOLS_STOCKS)
