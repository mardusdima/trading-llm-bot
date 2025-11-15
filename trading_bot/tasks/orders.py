from celery import shared_task
from trading_bot.core.trading_orchestrator import TradingOrchestrator
from trading_bot.logging.logger import logger
import os

SYMBOLS_CRYPTO = os.getenv("SYMBOLS_CRYPTO", "BTC/USDT,ETH/USDT").split(",")
SYMBOLS_STOCKS = os.getenv("SYMBOLS_STOCKS", "AAPL,MSFT").split(",")

@shared_task
def process_order_task(order_id):
    """Process a specific order (for future use)"""
    logger.info(f"Processing order {order_id}")
    # TODO: Implement order status checking and updates
    pass

@shared_task
def run_trading_cycle_crypto():
    """Run trading cycle for all crypto symbols"""
    logger.info("[Celery] Running trading cycle for crypto symbols")
    orchestrator = TradingOrchestrator(exchange_name="binance")
    
    for symbol in SYMBOLS_CRYPTO:
        try:
            result = orchestrator.execute_trading_cycle(symbol)
            logger.info(f"Trading cycle result for {symbol}: {result}")
        except Exception as e:
            logger.error(f"Trading cycle failed for {symbol}: {e}")

@shared_task
def run_trading_cycle_stocks():
    """Run trading cycle for all stock symbols"""
    logger.info("[Celery] Running trading cycle for stock symbols")
    orchestrator = TradingOrchestrator(exchange_name="alpaca")
    
    for symbol in SYMBOLS_STOCKS:
        try:
            result = orchestrator.execute_trading_cycle(symbol)
            logger.info(f"Trading cycle result for {symbol}: {result}")
        except Exception as e:
            logger.error(f"Trading cycle failed for {symbol}: {e}")
