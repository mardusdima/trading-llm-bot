import time
import os
from typing import Dict, Optional
from trading_bot.core.base import TradingBotError
from trading_bot.exchange_adapters.binance import BinanceAdapter
from trading_bot.exchange_adapters.alpaca import AlpacaAdapter
from trading_bot.logging.logger import logger

MAX_RETRIES = int(os.getenv("MAX_ORDER_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))  # seconds

class ExecutionEngine:
    def __init__(self, adapter):
        self.adapter = adapter
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY

    def send_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None, **kwargs) -> Dict:
        """
        Send order with retry logic and error handling.
        Returns order response dict.
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempting to {side} {amount} {symbol} at {price or 'market'}")
                order = self.adapter.create_order(symbol, side, amount, price, **kwargs)
                logger.info(f"Order placed successfully: {order.get('id', 'N/A')}")
                return order
            except Exception as e:
                last_error = e
                logger.warning(f"Order attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed for {symbol} {side} order")
                    raise TradingBotError(f"Failed to execute order after {self.max_retries} attempts: {e}")
        
        raise TradingBotError(f"Order execution failed: {last_error}")

    def cancel_order(self, order_id: str, symbol: str, **kwargs) -> Dict:
        """Cancel order with retry logic"""
        for attempt in range(self.max_retries):
            try:
                result = self.adapter.cancel_order(order_id, symbol, **kwargs)
                logger.info(f"Order {order_id} cancelled successfully")
                return result
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to cancel order {order_id}: {e}")
                    raise TradingBotError(f"Failed to cancel order: {e}")
        
        raise TradingBotError("Order cancellation failed")
