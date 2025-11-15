"""
Base classes and types for trading bot core functionality
"""

from abc import ABC, abstractmethod

class BaseExchangeAdapter(ABC):
    """All exchange/broker adapters must inherit from this."""
    @abstractmethod
    def authenticate(self, **kwargs):
        pass

    @abstractmethod
    def fetch_market_data(self, symbol: str, **kwargs):
        pass

    @abstractmethod
    def create_order(self, symbol: str, side: str, amount: float, price: float = None, **kwargs):
        pass

    @abstractmethod
    def cancel_order(self, order_id: str, **kwargs):
        pass

    @abstractmethod
    def fetch_balance(self, **kwargs):
        pass

class TradingBotError(Exception):
    """Base custom error class for trading bot."""
    pass
