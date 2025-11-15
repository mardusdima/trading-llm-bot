from trading_bot.exchange_adapters.binance import BinanceAdapter
from trading_bot.exchange_adapters.alpaca import AlpacaAdapter
from trading_bot.exchange_adapters.coinbase import CoinbaseAdapter
import pytest
import os
from unittest.mock import patch

import inspect

@pytest.mark.parametrize("cls", [BinanceAdapter, AlpacaAdapter, CoinbaseAdapter])
def test_adapter_methods_exist(cls):
    adapter = cls()
    for method in ["authenticate", "fetch_market_data", "create_order", "cancel_order", "fetch_balance"]:
        assert hasattr(adapter, method)
        assert inspect.ismethod(getattr(adapter, method)) or inspect.isfunction(getattr(adapter, method))

def test_binance_adapter_paper_trading():
    """Test Binance adapter in paper trading mode"""
    with patch.dict(os.environ, {"PAPER_TRADING": "1"}):
        adapter = BinanceAdapter()
        # In paper trading, create_order should return simulated order
        result = adapter.create_order("BTC/USDT", "buy", 1.0, 100.0)
        assert result["status"] == "filled"
        assert "paper_order" in result.get("id", "")

def test_alpaca_adapter_paper_trading():
    """Test Alpaca adapter in paper trading mode"""
    with patch.dict(os.environ, {"PAPER_TRADING": "1"}):
        adapter = AlpacaAdapter()
        result = adapter.create_order("AAPL", "buy", 1.0, 100.0)
        assert result["status"] == "filled"

@patch('trading_bot.exchange_adapters.binance.ccxt')
def test_binance_fetch_market_data(mock_ccxt):
    """Test Binance market data fetching"""
    from unittest.mock import Mock
    mock_exchange = Mock()
    mock_exchange.fetch_ohlcv.return_value = [[1609459200000, 100, 105, 99, 104, 1000]]
    mock_ccxt.binance.return_value = mock_exchange
    
    adapter = BinanceAdapter()
    adapter.exchange = mock_exchange
    data = adapter.fetch_market_data("BTC/USDT", timeframe="1m")
    assert len(data) > 0
