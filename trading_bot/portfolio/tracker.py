from typing import Dict, List
from datetime import datetime
from trading_bot.db.models import Trade
from trading_bot.db.session import get_session

class PortfolioTracker:
    def __init__(self):
        self.positions = {}  # symbol -> position dict
        self.closed_trades = []  # List of closed trade records
        self.initial_capital = 10000.0  # Starting capital (configurable)

    def update_positions(self, fills: List[Dict]):
        """
        Update positions based on trade fills.
        fills: List of dicts with keys: symbol, side, amount, price, order_id, timestamp
        """
        for fill in fills:
            symbol = fill.get('symbol')
            side = fill.get('side')
            amount = fill.get('amount', 0)
            price = fill.get('price', 0)
            order_id = fill.get('order_id')
            timestamp = fill.get('timestamp', datetime.utcnow())
            
            if symbol not in self.positions:
                self.positions[symbol] = {
                    'amount': 0,
                    'avg_entry_price': 0,
                    'side': side,
                    'entry_timestamp': timestamp,
                    'value': 0
                }
            
            pos = self.positions[symbol]
            
            if side == 'buy':
                if pos['amount'] <= 0:  # Opening or reversing long position
                    total_cost = (pos['amount'] * pos['avg_entry_price']) + (amount * price)
                    total_amount = pos['amount'] + amount
                    pos['avg_entry_price'] = total_cost / total_amount if total_amount > 0 else price
                    pos['amount'] = total_amount
                    pos['side'] = 'buy'
                else:  # Adding to long position
                    total_cost = (pos['amount'] * pos['avg_entry_price']) + (amount * price)
                    total_amount = pos['amount'] + amount
                    pos['avg_entry_price'] = total_cost / total_amount
                    pos['amount'] = total_amount
            else:  # sell
                if pos['amount'] >= 0:  # Closing long or opening short
                    if pos['amount'] > 0:  # Closing long position
                        close_amount = min(pos['amount'], amount)
                        realized_pnl = (price - pos['avg_entry_price']) * close_amount
                        pos['amount'] -= close_amount
                        if pos['amount'] == 0:
                            # Position closed
                            self.closed_trades.append({
                                'symbol': symbol,
                                'side': 'sell',
                                'amount': close_amount,
                                'entry_price': pos['avg_entry_price'],
                                'exit_price': price,
                                'realized_pnl': realized_pnl,
                                'timestamp': timestamp
                            })
                            del self.positions[symbol]
                        else:
                            # Partial close
                            self.closed_trades.append({
                                'symbol': symbol,
                                'side': 'sell',
                                'amount': close_amount,
                                'entry_price': pos['avg_entry_price'],
                                'exit_price': price,
                                'realized_pnl': realized_pnl,
                                'timestamp': timestamp
                            })
                    else:  # Opening short position
                        pos['amount'] -= amount
                        pos['avg_entry_price'] = price
                        pos['side'] = 'sell'
                else:  # Adding to short position
                    total_cost = abs(pos['amount']) * pos['avg_entry_price'] + amount * price
                    total_amount = abs(pos['amount']) + amount
                    pos['avg_entry_price'] = total_cost / total_amount
                    pos['amount'] = -total_amount
            
            # Update position value
            if symbol in self.positions:
                pos['value'] = abs(pos['amount']) * price

    def calculate_pnl(self, current_prices: Dict[str, float]) -> Dict:
        """
        Calculate realized and unrealized P&L.
        current_prices: dict of symbol -> current market price
        Returns dict with total_pnl, realized_pnl, unrealized_pnl, portfolio_value
        """
        realized_pnl = sum(trade.get('realized_pnl', 0) for trade in self.closed_trades)
        
        unrealized_pnl = 0.0
        total_position_value = 0.0
        
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.get('avg_entry_price', 0))
            if current_price == 0:
                continue
            
            entry_price = position['avg_entry_price']
            amount = position['amount']
            
            if amount > 0:  # Long position
                position_value = amount * current_price
                unrealized_pnl += (current_price - entry_price) * amount
            else:  # Short position
                position_value = abs(amount) * current_price
                unrealized_pnl += (entry_price - current_price) * abs(amount)
            
            total_position_value += position_value
            position['value'] = position_value
            position['current_price'] = current_price
        
        total_pnl = realized_pnl + unrealized_pnl
        portfolio_value = self.initial_capital + total_pnl
        
        return {
            'total_pnl': total_pnl,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'portfolio_value': portfolio_value,
            'total_position_value': total_position_value,
            'cash': self.initial_capital - total_position_value + realized_pnl,
            'positions': self.positions.copy(),
            'closed_trades_count': len(self.closed_trades)
        }

    def get_positions(self) -> Dict:
        """Get current positions"""
        return self.positions.copy()

    def get_peak_value(self) -> float:
        """Get peak portfolio value (for drawdown calculation)"""
        # This would ideally be tracked over time, but for now return current
        # In production, store peak values in DB
        return self.initial_capital * 1.1  # Placeholder
