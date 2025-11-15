import time
import os
from typing import Dict, Optional
from datetime import datetime
from trading_bot.core.base import TradingBotError
from trading_bot.exchange_adapters.binance import BinanceAdapter
from trading_bot.exchange_adapters.alpaca import AlpacaAdapter
from trading_bot.db.models import Order
from trading_bot.db.session import get_session
from trading_bot.logging.logger import logger

MAX_RETRIES = int(os.getenv("MAX_ORDER_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))  # seconds

class ExecutionEngine:
    def __init__(self, adapter, exchange_name: str = "binance"):
        self.adapter = adapter
        self.exchange_name = exchange_name
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY

    def send_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None, **kwargs) -> Dict:
        """
        Send order with retry logic and error handling.
        Returns order response dict with database order ID.
        """
        # Create order record in database
        order_type = 'limit' if price else 'market'
        db_order = Order(
            exchange=self.exchange_name,
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            status='pending'
        )
        
        with get_session() as session:
            session.add(db_order)
            session.commit()
            session.refresh(db_order)
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempting to {side} {amount} {symbol} at {price or 'market'}")
                exchange_order = self.adapter.create_order(symbol, side, amount, price, **kwargs)
                
                # Update order with exchange response
                with get_session() as session:
                    order = session.query(Order).filter_by(id=db_order.id).first()
                    if order:
                        order.exchange_order_id = str(exchange_order.get('id', ''))
                        order.status = exchange_order.get('status', 'filled')
                        order.filled_amount = exchange_order.get('filled', amount)
                        order.average_fill_price = exchange_order.get('price') or price
                        session.commit()
                
                logger.info(f"Order placed successfully: {exchange_order.get('id', 'N/A')}")
                return {
                    **exchange_order,
                    'db_order_id': db_order.id,
                    'exchange_order_id': exchange_order.get('id')
                }
            except Exception as e:
                last_error = e
                logger.warning(f"Order attempt {attempt + 1}/{self.max_retries} failed: {e}")
                
                # Update order status
                with get_session() as session:
                    order = session.query(Order).filter_by(id=db_order.id).first()
                    if order:
                        if attempt == self.max_retries - 1:
                            order.status = 'rejected'
                            order.error_message = str(e)
                        session.commit()
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed for {symbol} {side} order")
                    raise TradingBotError(f"Failed to execute order after {self.max_retries} attempts: {e}")
        
        raise TradingBotError(f"Order execution failed: {last_error}")

    def cancel_order(self, order_id: str, symbol: str, **kwargs) -> Dict:
        """Cancel order with retry logic and database tracking"""
        # Find order in database
        with get_session() as session:
            order = session.query(Order).filter_by(
                exchange_order_id=order_id,
                exchange=self.exchange_name
            ).first()
            if not order:
                # Try by database ID
                try:
                    order = session.query(Order).filter_by(id=int(order_id)).first()
                except:
                    pass
        
        for attempt in range(self.max_retries):
            try:
                result = self.adapter.cancel_order(order_id, symbol, **kwargs)
                
                # Update order status
                if order:
                    with get_session() as session:
                        db_order = session.query(Order).filter_by(id=order.id).first()
                        if db_order:
                            db_order.status = 'canceled'
                            session.commit()
                
                logger.info(f"Order {order_id} cancelled successfully")
                return result
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to cancel order {order_id}: {e}")
                    if order:
                        with get_session() as session:
                            db_order = session.query(Order).filter_by(id=order.id).first()
                            if db_order:
                                db_order.error_message = str(e)
                                session.commit()
                    raise TradingBotError(f"Failed to cancel order: {e}")
        
        raise TradingBotError("Order cancellation failed")
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get order status from database"""
        with get_session() as session:
            order = session.query(Order).filter_by(id=int(order_id)).first()
            if order:
                return {
                    'id': order.id,
                    'exchange_order_id': order.exchange_order_id,
                    'symbol': order.symbol,
                    'side': order.side,
                    'status': order.status,
                    'amount': order.amount,
                    'filled_amount': order.filled_amount,
                    'price': order.price,
                    'average_fill_price': order.average_fill_price,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'updated_at': order.updated_at.isoformat() if order.updated_at else None
                }
        return None
