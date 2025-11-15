import pytest
from datetime import datetime
from trading_bot.portfolio.tracker import PortfolioTracker

def test_portfolio_tracker_initialization():
    """Test PortfolioTracker initializes correctly"""
    tracker = PortfolioTracker(exchange="binance")
    assert tracker.exchange == "binance"
    assert tracker.initial_capital > 0
    assert isinstance(tracker.positions, dict)

def test_update_positions_buy():
    """Test updating positions with buy orders"""
    tracker = PortfolioTracker(exchange="binance")
    fills = [{
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'amount': 1.0,
        'price': 100.0,
        'order_id': 'order1',
        'timestamp': datetime.utcnow()
    }]
    
    tracker.update_positions(fills)
    assert 'BTC/USDT' in tracker.positions
    assert tracker.positions['BTC/USDT']['amount'] == 1.0
    assert tracker.positions['BTC/USDT']['avg_entry_price'] == 100.0

def test_update_positions_sell_close():
    """Test closing a position with sell order"""
    tracker = PortfolioTracker(exchange="binance")
    # First buy
    tracker.update_positions([{
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'amount': 1.0,
        'price': 100.0,
        'order_id': 'order1',
        'timestamp': datetime.utcnow()
    }])
    
    # Then sell to close
    tracker.update_positions([{
        'symbol': 'BTC/USDT',
        'side': 'sell',
        'amount': 1.0,
        'price': 110.0,
        'order_id': 'order2',
        'timestamp': datetime.utcnow()
    }])
    
    # Position should be closed
    assert 'BTC/USDT' not in tracker.positions
    assert len(tracker.closed_trades) == 1
    assert tracker.closed_trades[0]['realized_pnl'] == 10.0

def test_calculate_pnl():
    """Test P&L calculation"""
    tracker = PortfolioTracker(exchange="binance")
    # Open position
    tracker.update_positions([{
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'amount': 1.0,
        'price': 100.0,
        'order_id': 'order1',
        'timestamp': datetime.utcnow()
    }])
    
    # Calculate P&L with current price
    current_prices = {'BTC/USDT': 110.0}
    pnl_data = tracker.calculate_pnl(current_prices)
    
    assert pnl_data['unrealized_pnl'] == 10.0
    assert pnl_data['portfolio_value'] > tracker.initial_capital
    assert 'BTC/USDT' in pnl_data['positions']

def test_partial_close():
    """Test partial position close"""
    tracker = PortfolioTracker(exchange="binance")
    # Buy 2 units
    tracker.update_positions([{
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'amount': 2.0,
        'price': 100.0,
        'order_id': 'order1',
        'timestamp': datetime.utcnow()
    }])
    
    # Sell 1 unit (partial close)
    tracker.update_positions([{
        'symbol': 'BTC/USDT',
        'side': 'sell',
        'amount': 1.0,
        'price': 110.0,
        'order_id': 'order2',
        'timestamp': datetime.utcnow()
    }])
    
    # Should still have 1 unit
    assert tracker.positions['BTC/USDT']['amount'] == 1.0
    assert len(tracker.closed_trades) == 1

