import os
import ccxt
from trading_bot.core.base import BaseExchangeAdapter, TradingBotError

PAPER_TRADING = os.getenv("PAPER_TRADING", "1") != "0"

class BinanceAdapter(BaseExchangeAdapter):
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY", "")
        self.api_secret = os.getenv("BINANCE_API_SECRET", "")
        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True
        })

    def authenticate(self, **kwargs):
        # ccxt uses keys at init, so no-op
        return self.api_key != "" and self.api_secret != ""

    def fetch_market_data(self, symbol: str, timeframe: str = '1m', limit: int = 100, book: bool = False, **kwargs):
        if book:
            return self.exchange.fetch_order_book(symbol)
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def fetch_ticker(self, symbol: str):
        return self.exchange.fetch_ticker(symbol)

    def create_order(self, symbol: str, side: str, amount: float, price: float = None, **kwargs):
        if PAPER_TRADING:
            # Simulate order
            return {"id": "paper_order", "status": "filled", "symbol": symbol, "side": side, "amount": amount, "price": price}
        try:
            if price:
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            else:
                order = self.exchange.create_market_order(symbol, side, amount)
            return order
        except Exception as e:
            raise TradingBotError(f"Create order failed: {e}")

    def cancel_order(self, order_id: str, symbol: str = None, **kwargs):
        if PAPER_TRADING:
            return {"status": "canceled", "id": order_id}
        try:
            return self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            raise TradingBotError(f"Cancel order failed: {e}")

    def fetch_balance(self, **kwargs):
        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            raise TradingBotError(f"Fetch balance failed: {e}")
