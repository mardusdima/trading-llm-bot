"""
Backtesting framework for strategy validation on historical data
"""
import pandas as pd
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from trading_bot.strategy.sma_crossover import SMACrossoverStrategy
from trading_bot.risk.manager import RiskManager
from trading_bot.portfolio.tracker import PortfolioTracker
from trading_bot.logging.logger import logger

class BacktestResult:
    """Container for backtest results"""
    def __init__(self):
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_value = 0.0
        self.final_value = 0.0
        self.initial_capital = 0.0
        self.return_pct = 0.0
        self.sharpe_ratio = 0.0
        self.trades = []
        self.equity_curve = []

    def to_dict(self) -> Dict:
        """Convert results to dictionary"""
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.winning_trades / self.total_trades if self.total_trades > 0 else 0,
            "total_pnl": self.total_pnl,
            "max_drawdown": self.max_drawdown,
            "peak_value": self.peak_value,
            "final_value": self.final_value,
            "initial_capital": self.initial_capital,
            "return_pct": self.return_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "total_return": self.final_value - self.initial_capital
        }

class Backtester:
    """Backtesting engine for trading strategies"""
    
    def __init__(
        self,
        strategy: Callable,
        initial_capital: float = 10000.0,
        risk_manager: Optional[RiskManager] = None
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.risk_manager = risk_manager or RiskManager()
        self.portfolio_tracker = PortfolioTracker(exchange="backtest")
        self.portfolio_tracker.initial_capital = initial_capital
    
    def run(
        self,
        data: pd.DataFrame,
        symbol: str = "BTC/USDT",
        commission: float = 0.001,  # 0.1% commission
        slippage: float = 0.0005    # 0.05% slippage
    ) -> BacktestResult:
        """
        Run backtest on historical data.
        
        Args:
            data: DataFrame with columns: timestamp, open, high, low, close, volume
            symbol: Trading symbol
            commission: Commission rate (e.g., 0.001 = 0.1%)
            slippage: Slippage rate (e.g., 0.0005 = 0.05%)
        
        Returns:
            BacktestResult object with performance metrics
        """
        result = BacktestResult()
        result.initial_capital = self.initial_capital
        
        # Ensure data is sorted by timestamp
        if 'timestamp' in data.columns:
            data = data.sort_values('timestamp').reset_index(drop=True)
        
        # Generate signals
        if isinstance(self.strategy, SMACrossoverStrategy):
            signals = self.strategy.generate_signals(data['close'])
        else:
            # Generic strategy function
            signals = self.strategy(data)
        
        # Track equity curve
        equity_values = [self.initial_capital]
        peak_value = self.initial_capital
        max_drawdown = 0.0
        
        # Simulate trading
        position = None
        entry_price = 0.0
        entry_timestamp = None
        
        for i in range(len(data)):
            current_price = data.iloc[i]['close']
            signal = signals.iloc[i] if hasattr(signals, 'iloc') else signals[i]
            timestamp = data.iloc[i].get('timestamp', i)
            
            # Calculate current portfolio value
            current_prices = {symbol: current_price}
            pnl_data = self.portfolio_tracker.calculate_pnl(current_prices)
            portfolio_value = pnl_data['portfolio_value']
            equity_values.append(portfolio_value)
            
            # Update peak and drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value
            drawdown = (peak_value - portfolio_value) / peak_value if peak_value > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            
            # Handle signals
            if signal > 0 and position != 'long':  # Buy signal
                if position == 'short':
                    # Close short position
                    self._close_position(symbol, current_price, timestamp, commission, slippage, result)
                
                # Open long position
                if self._can_open_position(symbol, current_price, portfolio_value, peak_value):
                    position = 'long'
                    entry_price = current_price * (1 + slippage)  # Account for slippage
                    entry_timestamp = timestamp
                    self._open_position(symbol, 'buy', current_price, entry_price, timestamp, result)
            
            elif signal < 0 and position != 'short':  # Sell signal
                if position == 'long':
                    # Close long position
                    self._close_position(symbol, current_price, timestamp, commission, slippage, result)
                
                # Open short position (if supported)
                # For simplicity, we'll just close long positions
                if position == 'long':
                    position = None
                    entry_price = 0.0
                    entry_timestamp = None
        
        # Close any open positions at end
        if position:
            final_price = data.iloc[-1]['close']
            final_timestamp = data.iloc[-1].get('timestamp', len(data) - 1)
            self._close_position(symbol, final_price, final_timestamp, commission, slippage, result)
        
        # Calculate final metrics
        final_pnl = self.portfolio_tracker.calculate_pnl({symbol: data.iloc[-1]['close']})
        result.final_value = final_pnl['portfolio_value']
        result.total_pnl = final_pnl['total_pnl']
        result.peak_value = peak_value
        result.max_drawdown = max_drawdown
        result.return_pct = ((result.final_value - self.initial_capital) / self.initial_capital) * 100
        result.equity_curve = equity_values
        
        # Calculate Sharpe ratio (simplified)
        if len(equity_values) > 1:
            returns = pd.Series(equity_values).pct_change().dropna()
            if len(returns) > 0 and returns.std() > 0:
                result.sharpe_ratio = (returns.mean() / returns.std()) * (252 ** 0.5)  # Annualized
        
        return result
    
    def _can_open_position(self, symbol: str, price: float, portfolio_value: float, peak_value: float) -> bool:
        """Check if position can be opened based on risk management"""
        positions = self.portfolio_tracker.get_positions()
        amount = (portfolio_value * 0.1) / price  # 10% of portfolio
        
        is_valid, _ = self.risk_manager.validate_trade(
            symbol, 'buy', amount, price, positions, portfolio_value, peak_value
        )
        return is_valid
    
    def _open_position(self, symbol: str, side: str, market_price: float, entry_price: float, 
                      timestamp, result: BacktestResult):
        """Open a position"""
        amount = (self.portfolio_tracker.initial_capital * 0.1) / entry_price
        fill = {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': entry_price,
            'order_id': f'backtest_{len(result.trades)}',
            'timestamp': timestamp
        }
        self.portfolio_tracker.update_positions([fill])
    
    def _close_position(self, symbol: str, market_price: float, timestamp, commission: float, 
                       slippage: float, result: BacktestResult):
        """Close a position"""
        positions = self.portfolio_tracker.get_positions()
        if symbol not in positions:
            return
        
        position = positions[symbol]
        amount = abs(position['amount'])
        entry_price = position['avg_entry_price']
        
        # Apply slippage
        if position['side'] == 'buy':
            exit_price = market_price * (1 - slippage)
        else:
            exit_price = market_price * (1 + slippage)
        
        # Calculate P&L
        if position['side'] == 'buy':
            pnl = (exit_price - entry_price) * amount
        else:
            pnl = (entry_price - exit_price) * amount
        
        # Apply commission
        commission_cost = (entry_price + exit_price) * amount * commission
        pnl -= commission_cost
        
        # Record trade
        trade_record = {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'amount': amount,
            'pnl': pnl,
            'entry_time': position.get('entry_timestamp'),
            'exit_time': timestamp
        }
        result.trades.append(trade_record)
        result.total_trades += 1
        
        if pnl > 0:
            result.winning_trades += 1
        else:
            result.losing_trades += 1
        
        # Close position
        side = 'sell' if position['side'] == 'buy' else 'buy'
        fill = {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': exit_price,
            'order_id': f'backtest_close_{len(result.trades)}',
            'timestamp': timestamp
        }
        self.portfolio_tracker.update_positions([fill])

def run_backtest(
    data: pd.DataFrame,
    strategy_class=SMACrossoverStrategy,
    strategy_params: Optional[Dict] = None,
    initial_capital: float = 10000.0,
    symbol: str = "BTC/USDT"
) -> Dict:
    """
    Convenience function to run a backtest.
    
    Args:
        data: Historical price data DataFrame
        strategy_class: Strategy class to use
        strategy_params: Parameters for strategy initialization
        initial_capital: Starting capital
        symbol: Trading symbol
    
    Returns:
        Dictionary with backtest results
    """
    strategy_params = strategy_params or {}
    strategy = strategy_class(**strategy_params)
    
    backtester = Backtester(strategy, initial_capital=initial_capital)
    result = backtester.run(data, symbol=symbol)
    
    return result.to_dict()

