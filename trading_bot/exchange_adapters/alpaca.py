import os
import requests
from trading_bot.core.base import BaseExchangeAdapter, TradingBotError

PAPER_TRADING = os.getenv("PAPER_TRADING", "1") != "0"

class AlpacaAdapter(BaseExchangeAdapter):
    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY", "")
        self.api_secret = os.getenv("ALPACA_API_SECRET", "")
        self.base_url = os.getenv("ALPACA_API_URL", "https://paper-api.alpaca.markets") if PAPER_TRADING else "https://api.alpaca.markets"

    def authenticate(self, **kwargs):
        return self.api_key != "" and self.api_secret != ""

    def fetch_market_data(self, symbol: str, timeframe: str='1Min', limit: int=100, book: bool=False, **kwargs):
        if book:
            # Alpaca does not offer public orderbook; stub for interface
            return {"error": "Order book not available"}
        # Get bars
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
        headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret
        }
        params = {'timeframe': timeframe, 'limit': limit}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise TradingBotError(f"Alpaca fetch_market_data failed: {resp.text}")
        return resp.json()

    def fetch_ticker(self, symbol: str):
        # Alpaca does not have 'fetch_ticker', mimic with latest trade
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/trades/latest"
        headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise TradingBotError(f"Fetch ticker failed: {resp.text}")
        return resp.json()

    def create_order(self, symbol: str, side: str, amount: float, price: float = None, **kwargs):
        if PAPER_TRADING:
            return {"id": "paper_order", "symbol": symbol, "side": side, "qty": amount, "price": price, "status": "filled"}
        url = f"{self.base_url}/v2/orders"
        headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret
        }
        data = {
            "symbol": symbol,
            "qty": amount,
            "side": side,
            "type": "limit" if price else "market",
            "time_in_force": "gtc"
        }
        if price:
            data["limit_price"] = price
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code not in [200,201]:
            raise TradingBotError(f"Alpaca create_order failed: {resp.text}")
        return resp.json()

    def cancel_order(self, order_id: str, symbol: str=None, **kwargs):
        if PAPER_TRADING:
            return {"id": order_id, "status": "canceled"}
        url = f"{self.base_url}/v2/orders/{order_id}"
        headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret
        }
        resp = requests.delete(url, headers=headers)
        if resp.status_code != 204:
            raise TradingBotError(f"Alpaca cancel_order failed: {resp.text}")
        return {"status": "canceled", "id": order_id}

    def fetch_balance(self, **kwargs):
        url = f"{self.base_url}/v2/account"
        headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise TradingBotError(f"Fetch balance failed: {resp.text}")
        return resp.json()
