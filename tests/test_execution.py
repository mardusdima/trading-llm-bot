import pytest
from unittest.mock import Mock, patch
from trading_bot.execution.engine import ExecutionEngine
from trading_bot.core.base import TradingBotError

def test_execution_engine_initialization():
    """Test ExecutionEngine initializes correctly"""
    adapter = Mock()
    engine = ExecutionEngine(adapter, exchange_name="binance")
    assert engine.adapter == adapter
    assert engine.max_retries > 0
    assert engine.retry_delay > 0

@patch('trading_bot.execution.engine.get_session')
def test_send_order_success(mock_session):
    """Test successful order execution"""
    adapter = Mock()
    adapter.create_order.return_value = {
        'id': 'test_order_123',
        'status': 'filled',
        'price': 100.0
    }
    
    # Mock database session
    mock_db_order = Mock()
    mock_db_order.id = 1
    mock_session.return_value.__enter__.return_value.add = Mock()
    mock_session.return_value.__enter__.return_value.commit = Mock()
    mock_session.return_value.__enter__.return_value.refresh = Mock()
    mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = mock_db_order
    
    engine = ExecutionEngine(adapter, exchange_name="binance")
    result = engine.send_order("BTC/USDT", "buy", 1.0, 100.0)
    
    assert result['id'] == 'test_order_123'
    assert result['status'] == 'filled'
    adapter.create_order.assert_called_once()

@patch('trading_bot.execution.engine.get_session')
def test_send_order_retry(mock_session):
    """Test order execution with retries"""
    adapter = Mock()
    adapter.create_order.side_effect = [Exception("Network error"), {
        'id': 'test_order_123',
        'status': 'filled'
    }]
    
    mock_db_order = Mock()
    mock_db_order.id = 1
    mock_session.return_value.__enter__.return_value.add = Mock()
    mock_session.return_value.__enter__.return_value.commit = Mock()
    mock_session.return_value.__enter__.return_value.refresh = Mock()
    mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = mock_db_order
    
    engine = ExecutionEngine(adapter, exchange_name="binance")
    result = engine.send_order("BTC/USDT", "buy", 1.0, 100.0)
    
    assert result['id'] == 'test_order_123'
    assert adapter.create_order.call_count == 2

@patch('trading_bot.execution.engine.get_session')
def test_send_order_max_retries_exceeded(mock_session):
    """Test order execution fails after max retries"""
    adapter = Mock()
    adapter.create_order.side_effect = Exception("Persistent error")
    
    mock_db_order = Mock()
    mock_db_order.id = 1
    mock_session.return_value.__enter__.return_value.add = Mock()
    mock_session.return_value.__enter__.return_value.commit = Mock()
    mock_session.return_value.__enter__.return_value.refresh = Mock()
    mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = mock_db_order
    
    engine = ExecutionEngine(adapter, exchange_name="binance")
    
    with pytest.raises(TradingBotError):
        engine.send_order("BTC/USDT", "buy", 1.0, 100.0)

