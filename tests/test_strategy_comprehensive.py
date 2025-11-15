import pytest
import pandas as pd
from datetime import datetime, timedelta
from trading_bot.strategy.sma_crossover import SMACrossoverStrategy

def test_sma_crossover_initialization():
    """Test SMA strategy initializes with custom windows"""
    strategy = SMACrossoverStrategy(short_window=10, long_window=20)
    assert strategy.short_window == 10
    assert strategy.long_window == 20

def test_generate_signals_bullish_crossover():
    """Test signal generation for bullish crossover"""
    strategy = SMACrossoverStrategy(short_window=2, long_window=4)
    # Create data where short SMA crosses above long SMA
    data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    signals = strategy.generate_signals(data)
    
    # Should have signals (1 for buy, -1 for sell, 0 for hold)
    assert len(signals) == len(data)
    assert signals.dtype in [int, float]

def test_generate_signals_bearish_crossover():
    """Test signal generation for bearish crossover"""
    strategy = SMACrossoverStrategy(short_window=2, long_window=4)
    # Create declining data
    data = pd.Series([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    signals = strategy.generate_signals(data)
    
    assert len(signals) == len(data)

def test_get_signal_from_db_insufficient_data():
    """Test signal generation with insufficient data"""
    strategy = SMACrossoverStrategy(short_window=50, long_window=200)
    # Should return 0 (hold) when not enough data
    signal = strategy.get_signal_from_db("BTC/USDT", "binance", lookback=10)
    assert signal == 0

def test_sma_crossover_with_realistic_data():
    """Test with realistic price series"""
    strategy = SMACrossoverStrategy(short_window=5, long_window=10)
    # Simulate price movement
    prices = pd.Series([100, 102, 101, 103, 105, 107, 106, 108, 110, 112, 115, 118, 120])
    signals = strategy.generate_signals(prices)
    
    assert len(signals) == len(prices)
    # All signals should be valid (0, 1, or -1)
    assert all(s in [0, 1, -1] for s in signals)

