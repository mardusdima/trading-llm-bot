"""
Main trading orchestrator that wires together:
Strategy -> Risk Management -> Execution -> Portfolio Tracking
"""
import os
from typing import Dict, Optional
from datetime import datetime
from trading_bot.strategy.sma_crossover import SMACrossoverStrategy
from trading_bot.risk.manager import RiskManager
from trading_bot.execution.engine import ExecutionEngine
from trading_bot.portfolio.tracker import PortfolioTracker
from trading_bot.exchange_adapters.binance import BinanceAdapter
from trading_bot.exchange_adapters.alpaca import AlpacaAdapter
from trading_bot.logging.logger import logger
from trading_bot.db.models import Trade
from trading_bot.db.session import get_session

class TradingOrchestrator:
    def __init__(self, exchange_name: str = "binance"):
        self.exchange_name = exchange_name
        if exchange_name == "binance":
            self.adapter = BinanceAdapter()
        elif exchange_name == "alpaca":
            self.adapter = AlpacaAdapter()
        else:
            raise ValueError(f"Unsupported exchange: {exchange_name}")
        
        self.strategy = SMACrossoverStrategy()
        self.risk_manager = RiskManager()
        self.execution_engine = ExecutionEngine(self.adapter)
        self.portfolio_tracker = PortfolioTracker()
    
    def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        try:
            ticker = self.adapter.fetch_ticker(symbol)
            return float(ticker.get('last') or ticker.get('close') or ticker.get('price', 0))
        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")
            return 0.0
    
    def execute_trading_cycle(self, symbol: str, timeframe: str = '1m') -> Dict:
        """
        Complete trading cycle:
        1. Get strategy signal
        2. Check risk
        3. Execute order if approved
        4. Update portfolio
        5. Log trade
        """
        try:
            # Step 1: Get strategy signal
            signal = self.strategy.get_signal_from_db(symbol, self.exchange_name, timeframe)
            logger.info(f"Strategy signal for {symbol}: {signal}")
            
            if signal == 0:
                return {"status": "hold", "reason": "No signal"}
            
            # Step 2: Get current price and portfolio state
            current_price = self.get_current_price(symbol)
            if current_price == 0:
                return {"status": "error", "reason": "Could not fetch current price"}
            
            positions = self.portfolio_tracker.get_positions()
            pnl_data = self.portfolio_tracker.calculate_pnl({symbol: current_price})
            portfolio_value = pnl_data['portfolio_value']
            peak_value = self.portfolio_tracker.get_peak_value()
            
            # Step 3: Determine order parameters
            side = "buy" if signal > 0 else "sell"
            # Calculate position size (simple: use fixed amount or percentage of portfolio)
            position_size_pct = float(os.getenv("POSITION_SIZE_PCT", "10.0"))  # 10% of portfolio
            amount = (portfolio_value * position_size_pct / 100) / current_price
            
            # Step 4: Risk validation
            is_valid, reason = self.risk_manager.validate_trade(
                symbol=symbol,
                side=side,
                amount=amount,
                price=current_price,
                current_positions=positions,
                portfolio_value=portfolio_value,
                peak_value=peak_value
            )
            
            if not is_valid:
                logger.warning(f"Trade rejected by risk manager: {reason}")
                return {"status": "rejected", "reason": reason}
            
            # Step 5: Execute order
            logger.info(f"Executing {side} order for {amount} {symbol} at {current_price}")
            order = self.execution_engine.send_order(
                symbol=symbol,
                side=side,
                amount=amount,
                price=current_price
            )
            
            # Step 6: Update portfolio
            fill = {
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': current_price,
                'order_id': order.get('id', 'unknown'),
                'timestamp': datetime.utcnow()
            }
            self.portfolio_tracker.update_positions([fill])
            
            # Step 7: Log trade to database
            self._log_trade_to_db(order, symbol, side, amount, current_price)
            
            return {
                "status": "executed",
                "order_id": order.get('id'),
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": current_price
            }
            
        except Exception as e:
            logger.error(f"Trading cycle failed for {symbol}: {e}")
            return {"status": "error", "reason": str(e)}
    
    def _log_trade_to_db(self, order: Dict, symbol: str, side: str, amount: float, price: float):
        """Audit log trade to database"""
        try:
            trade = Trade(
                symbol=symbol,
                order_id=str(order.get('id', 'unknown')),
                side=side,
                amount=amount,
                price=price,
                timestamp=datetime.utcnow(),
                status=order.get('status', 'filled')
            )
            with get_session() as session:
                session.add(trade)
        except Exception as e:
            logger.error(f"Failed to log trade to DB: {e}")
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        positions = self.portfolio_tracker.get_positions()
        current_prices = {}
        for symbol in positions.keys():
            current_prices[symbol] = self.get_current_price(symbol)
        
        pnl_data = self.portfolio_tracker.calculate_pnl(current_prices)
        return pnl_data

