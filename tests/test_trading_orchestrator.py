import pytest
from unittest.mock import Mock, patch
from trading_bot.core.trading_orchestrator import TradingOrchestrator

@patch('trading_bot.core.trading_orchestrator.BinanceAdapter')
def test_trading_orchestrator_initialization(mock_adapter):
    """Test TradingOrchestrator initializes correctly"""
    orchestrator = TradingOrchestrator(exchange_name="binance")
    assert orchestrator.exchange_name == "binance"
    assert orchestrator.strategy is not None
    assert orchestrator.risk_manager is not None
    assert orchestrator.execution_engine is not None
    assert orchestrator.portfolio_tracker is not None

@patch('trading_bot.core.trading_orchestrator.TradingOrchestrator.get_current_price')
@patch('trading_bot.core.trading_orchestrator.SMACrossoverStrategy')
@patch('trading_bot.core.trading_orchestrator.RiskManager')
@patch('trading_bot.core.trading_orchestrator.ExecutionEngine')
def test_execute_trading_cycle_hold_signal(mock_execution, mock_risk, mock_strategy, mock_price):
    """Test trading cycle with hold signal"""
    # Setup mocks
    mock_strategy_instance = Mock()
    mock_strategy_instance.get_signal_from_db.return_value = 0  # Hold signal
    mock_strategy.return_value = mock_strategy_instance
    
    orchestrator = TradingOrchestrator(exchange_name="binance")
    orchestrator.strategy = mock_strategy_instance
    
    result = orchestrator.execute_trading_cycle("BTC/USDT")
    assert result["status"] == "hold"

@patch('trading_bot.core.trading_orchestrator.PortfolioTracker')
@patch('trading_bot.core.trading_orchestrator.TradingOrchestrator.get_current_price')
@patch('trading_bot.core.trading_orchestrator.SMACrossoverStrategy')
@patch('trading_bot.core.trading_orchestrator.RiskManager')
@patch('trading_bot.core.trading_orchestrator.ExecutionEngine')
@patch('trading_bot.core.trading_orchestrator.BinanceAdapter')
def test_execute_trading_cycle_risk_rejection(mock_adapter, mock_execution, mock_risk, mock_strategy, mock_price, mock_portfolio):
    """Test trading cycle with risk rejection"""
    from unittest.mock import MagicMock
    # Setup mocks
    mock_strategy_instance = Mock()
    mock_strategy_instance.get_signal_from_db.return_value = 1  # Buy signal
    mock_strategy.return_value = mock_strategy_instance
    
    mock_risk_instance = Mock()
    mock_risk_instance.validate_trade.return_value = (False, "Position limit exceeded")
    mock_risk.return_value = mock_risk_instance
    
    mock_price.return_value = 100.0
    
    # Mock portfolio tracker
    mock_portfolio_instance = MagicMock()
    mock_portfolio_instance.get_positions.return_value = {}
    mock_portfolio_instance.calculate_pnl.return_value = {'portfolio_value': 10000.0}
    mock_portfolio_instance.get_peak_value.return_value = 10000.0
    mock_portfolio.return_value = mock_portfolio_instance
    
    orchestrator = TradingOrchestrator(exchange_name="binance")
    orchestrator.strategy = mock_strategy_instance
    orchestrator.risk_manager = mock_risk_instance
    orchestrator.portfolio_tracker = mock_portfolio_instance
    
    result = orchestrator.execute_trading_cycle("BTC/USDT")
    assert result["status"] == "rejected"
    assert "limit" in result["reason"].lower()

def test_get_current_price():
    """Test getting current price"""
    with patch('trading_bot.core.trading_orchestrator.BinanceAdapter') as mock_adapter_class:
        mock_adapter = Mock()
        mock_adapter.fetch_ticker.return_value = {'last': 100.0}
        mock_adapter_class.return_value = mock_adapter
        
        orchestrator = TradingOrchestrator(exchange_name="binance")
        orchestrator.adapter = mock_adapter
        
        price = orchestrator.get_current_price("BTC/USDT")
        assert price == 100.0

