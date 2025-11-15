import os
from typing import Dict, Optional

MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "1000.0"))  # USD
MAX_DRAWDOWN_PCT = float(os.getenv("MAX_DRAWDOWN_PCT", "10.0"))  # 10%
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "2.0"))  # 2%

class RiskManager:
    def __init__(self):
        self.max_position_size = MAX_POSITION_SIZE
        self.max_drawdown_pct = MAX_DRAWDOWN_PCT
        self.stop_loss_pct = STOP_LOSS_PCT

    def check_position_limit(self, symbol: str, amount: float, price: float, current_positions: Dict) -> bool:
        """Check if position size exceeds limit"""
        position_value = amount * price
        if position_value > self.max_position_size:
            return False
        # Check total exposure across all positions
        total_exposure = sum(pos.get('value', 0) for pos in current_positions.values())
        if total_exposure + position_value > self.max_position_size * 5:  # 5x max single position
            return False
        return True

    def check_stop_loss(self, entry_price: float, current_price: float, side: str) -> bool:
        """Check if stop-loss would be triggered"""
        if side == 'buy':
            loss_pct = ((entry_price - current_price) / entry_price) * 100
        else:  # sell
            loss_pct = ((current_price - entry_price) / entry_price) * 100
        return loss_pct <= self.stop_loss_pct

    def check_max_drawdown(self, portfolio_value: float, peak_value: float) -> bool:
        """Check if portfolio drawdown exceeds max allowed"""
        if peak_value == 0:
            return True
        drawdown_pct = ((peak_value - portfolio_value) / peak_value) * 100
        return drawdown_pct <= self.max_drawdown_pct

    def validate_trade(self, symbol: str, side: str, amount: float, price: float, 
                      current_positions: Dict, portfolio_value: float, peak_value: float) -> tuple:
        """
        Comprehensive trade validation.
        Returns (is_valid, reason)
        """
        # Check position limits
        if not self.check_position_limit(symbol, amount, price, current_positions):
            return False, f"Position size {amount * price} exceeds limit {self.max_position_size}"
        
        # Check max drawdown
        if not self.check_max_drawdown(portfolio_value, peak_value):
            return False, f"Portfolio drawdown exceeds max {self.max_drawdown_pct}%"
        
        # Check if we already have a position in this symbol (optional: prevent over-exposure)
        if symbol in current_positions:
            existing_value = current_positions[symbol].get('value', 0)
            new_value = amount * price
            if existing_value + new_value > self.max_position_size * 2:
                return False, f"Total exposure for {symbol} would exceed 2x max position size"
        
        return True, "OK"

    def evaluate_position(self, position: Dict) -> bool:
        """Evaluate if an existing position should be closed due to risk"""
        entry_price = position.get('entry_price', 0)
        current_price = position.get('current_price', 0)
        side = position.get('side', 'buy')
        
        if entry_price == 0 or current_price == 0:
            return False
        
        return self.check_stop_loss(entry_price, current_price, side)

    def check_drawdown(self, portfolio):
        """Legacy method for compatibility"""
        portfolio_value = portfolio.get('total_value', 0)
        peak_value = portfolio.get('peak_value', portfolio_value)
        return self.check_max_drawdown(portfolio_value, peak_value)
