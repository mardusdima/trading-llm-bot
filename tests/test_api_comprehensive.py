import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from trading_bot.api.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_ping_endpoint():
    """Test ping endpoint"""
    response = client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data

@patch('trading_bot.api.main.TradingOrchestrator')
def test_execute_trade_endpoint(mock_orchestrator):
    """Test trade execution endpoint"""
    mock_instance = Mock()
    mock_instance.execute_trading_cycle.return_value = {
        "status": "executed",
        "order_id": "test123"
    }
    mock_orchestrator.return_value = mock_instance
    
    response = client.post("/api/trade/execute", json={
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "timeframe": "1m"
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "executed"

@patch('trading_bot.api.main.TradingOrchestrator')
def test_get_portfolio_summary(mock_orchestrator):
    """Test portfolio summary endpoint"""
    mock_instance = Mock()
    mock_instance.get_portfolio_summary.return_value = {
        "portfolio_value": 10000.0,
        "total_pnl": 100.0
    }
    mock_orchestrator.return_value = mock_instance
    
    response = client.get("/api/portfolio/summary?exchange=binance")
    assert response.status_code == 200
    data = response.json()
    assert "portfolio_value" in data

@patch('trading_bot.api.main.get_session')
def test_get_trade_history(mock_session):
    """Test trade history endpoint"""
    mock_trade = Mock()
    mock_trade.id = 1
    mock_trade.symbol = "BTC/USDT"
    mock_trade.side = "buy"
    mock_trade.amount = 1.0
    mock_trade.price = 100.0
    mock_trade.timestamp = None
    mock_trade.status = "filled"
    
    mock_session.return_value.__enter__.return_value.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_trade]
    
    response = client.get("/api/trades/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "symbol" in data[0]

@patch('trading_bot.api.main.get_session')
def test_list_orders(mock_session):
    """Test list orders endpoint"""
    mock_order = Mock()
    mock_order.id = 1
    mock_order.exchange_order_id = "ex123"
    mock_order.symbol = "BTC/USDT"
    mock_order.side = "buy"
    mock_order.status = "filled"
    mock_order.amount = 1.0
    mock_order.filled_amount = 1.0
    mock_order.price = 100.0
    mock_order.created_at = None
    
    mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_order]
    
    response = client.get("/api/orders?exchange=binance")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

