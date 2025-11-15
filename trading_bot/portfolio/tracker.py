from typing import Dict, List, Optional
from datetime import datetime
from trading_bot.db.models import Trade, Position, Portfolio
from trading_bot.db.session import get_session
from trading_bot.logging.logger import logger

class PortfolioTracker:
    def __init__(self, exchange: str = "binance"):
        self.exchange = exchange
        self.positions = {}  # symbol -> position dict
        self.closed_trades = []  # List of closed trade records
        self.initial_capital = 10000.0  # Starting capital (configurable)
        self._load_from_db()

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
        
        # Persist to database after updates
        self._save_to_db()

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
        
        pnl_data = {
            'total_pnl': total_pnl,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'portfolio_value': portfolio_value,
            'total_position_value': total_position_value,
            'cash': self.initial_capital - total_position_value + realized_pnl,
            'positions': self.positions.copy(),
            'closed_trades_count': len(self.closed_trades)
        }
        
        # Persist to database
        self._save_to_db(pnl_data)
        
        return pnl_data

    def get_positions(self) -> Dict:
        """Get current positions"""
        return self.positions.copy()

    def get_peak_value(self) -> float:
        """Get peak portfolio value (for drawdown calculation)"""
        with get_session() as session:
            portfolio = session.query(Portfolio).filter_by(exchange=self.exchange).first()
            if portfolio:
                return portfolio.peak_value
            return self.initial_capital

    def _load_from_db(self):
        """Load portfolio and positions from database"""
        try:
            with get_session() as session:
                # Load portfolio
                portfolio = session.query(Portfolio).filter_by(exchange=self.exchange).first()
                if portfolio:
                    self.initial_capital = portfolio.initial_capital
                
                # Load positions
                positions = session.query(Position).filter_by(exchange=self.exchange).all()
                for pos in positions:
                    self.positions[pos.symbol] = {
                        'amount': pos.amount,
                        'avg_entry_price': pos.avg_entry_price,
                        'side': pos.side,
                        'entry_timestamp': pos.entry_timestamp,
                        'value': abs(pos.amount) * (pos.current_price or pos.avg_entry_price),
                        'current_price': pos.current_price,
                        'unrealized_pnl': pos.unrealized_pnl
                    }
                logger.info(f"Loaded {len(self.positions)} positions from DB for {self.exchange}")
        except Exception as e:
            logger.warning(f"Failed to load portfolio from DB: {e}, starting fresh")

    def _save_to_db(self, pnl_data: Optional[Dict] = None):
        """Save portfolio and positions to database"""
        try:
            with get_session() as session:
                # Save/update portfolio
                portfolio = session.query(Portfolio).filter_by(exchange=self.exchange).first()
                if not portfolio:
                    portfolio = Portfolio(
                        exchange=self.exchange,
                        initial_capital=self.initial_capital,
                        current_value=self.initial_capital,
                        peak_value=self.initial_capital
                    )
                    session.add(portfolio)
                
                if pnl_data:
                    portfolio.current_value = pnl_data.get('portfolio_value', portfolio.current_value)
                    portfolio.total_pnl = pnl_data.get('total_pnl', 0)
                    portfolio.realized_pnl = pnl_data.get('realized_pnl', 0)
                    portfolio.unrealized_pnl = pnl_data.get('unrealized_pnl', 0)
                    if portfolio.current_value > portfolio.peak_value:
                        portfolio.peak_value = portfolio.current_value
                
                # Save/update positions
                db_positions = {p.symbol: p for p in session.query(Position).filter_by(exchange=self.exchange).all()}
                
                for symbol, pos_data in self.positions.items():
                    if symbol in db_positions:
                        db_pos = db_positions[symbol]
                        db_pos.amount = pos_data['amount']
                        db_pos.avg_entry_price = pos_data['avg_entry_price']
                        db_pos.side = pos_data['side']
                        db_pos.current_price = pos_data.get('current_price')
                        db_pos.unrealized_pnl = pos_data.get('unrealized_pnl', 0)
                        db_pos.updated_at = datetime.utcnow()
                    else:
                        db_pos = Position(
                            exchange=self.exchange,
                            symbol=symbol,
                            amount=pos_data['amount'],
                            avg_entry_price=pos_data['avg_entry_price'],
                            side=pos_data['side'],
                            entry_timestamp=pos_data.get('entry_timestamp', datetime.utcnow()),
                            current_price=pos_data.get('current_price'),
                            unrealized_pnl=pos_data.get('unrealized_pnl', 0)
                        )
                        session.add(db_pos)
                
                # Remove closed positions
                for symbol in list(db_positions.keys()):
                    if symbol not in self.positions:
                        session.delete(db_positions[symbol])
                
                session.commit()
        except Exception as e:
            logger.error(f"Failed to save portfolio to DB: {e}")
            raise
