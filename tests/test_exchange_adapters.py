from trading_bot.exchange_adapters.binance import BinanceAdapter
from trading_bot.exchange_adapters.alpaca import AlpacaAdapter
import pytest

import inspect

@pytest.mark.parametrize("cls", [BinanceAdapter, AlpacaAdapter])
def test_adapter_methods_exist(cls):
    adapter = cls()
    for method in ["authenticate", "fetch_market_data", "create_order", "cancel_order", "fetch_balance"]:
        assert hasattr(adapter, method)
        assert inspect.ismethod(getattr(adapter, method)) or inspect.isfunction(getattr(adapter, method))
