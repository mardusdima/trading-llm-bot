import os
import ccxt
from trading_bot.core.base import BaseExchangeAdapter, TradingBotError

PAPER_TRADING = os.getenv("PAPER_TRADING", "1") != "0"

class CoinbaseAdapter(BaseExchangeAdapter):
    def __init__(self):
        self.api_key = os.getenv("COINBASE_API_KEY", "")
        self.api_secret = os.getenv("COINBASE_API_SECRET", "")
        self.passphrase = os.getenv("COINBASE_PASSPHRASE", "")
        self.exchange = ccxt.coinbasepro({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'password': self.passphrase,
            'enableRateLimit': True,
            'sandbox': PAPER_TRADING  # Use sandbox for paper trading
        })

    def authenticate(self, **kwargs):
        """Authenticate with Coinbase Pro"""
        return self.api_key != "" and self.api_secret != "" and self.passphrase != ""

    def fetch_market_data(self, symbol: str, timeframe: str = '1m', limit: int = 100, book: bool = False, **kwargs):
        """Fetch market data (candles or order book)"""
        if book:
            return self.exchange.fetch_order_book(symbol)
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def fetch_ticker(self, symbol: str):
        """Fetch latest ticker data"""
        return self.exchange.fetch_ticker(symbol)

    def create_order(self, symbol: str, side: str, amount: float, price: float = None, **kwargs):
        """Create an order (paper or live based on PAPER_TRADING env)"""
        if PAPER_TRADING:
            # Simulate order for paper trading
            return {
                "id": f"paper_order_{symbol}_{side}",
                "status": "filled",
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": price or self.fetch_ticker(symbol).get('last', 0)
            }
        try:
            if price:
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            else:
                order = self.exchange.create_market_order(symbol, side, amount)
            return order
        except Exception as e:
            raise TradingBotError(f"Coinbase create order failed: {e}")

    def cancel_order(self, order_id: str, symbol: str = None, **kwargs):
        """Cancel an order"""
        if PAPER_TRADING:
            return {"status": "canceled", "id": order_id}
        try:
            return self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            raise TradingBotError(f"Coinbase cancel order failed: {e}")

    def fetch_balance(self, **kwargs):
        """Fetch account balance"""
        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            raise TradingBotError(f"Coinbase fetch balance failed: {e}")

