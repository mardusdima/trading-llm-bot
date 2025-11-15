import pytest
from unittest.mock import Mock, patch
from trading_bot.data.ingestion import DataIngestion

def test_data_ingestion_initialization():
    """Test DataIngestion initializes correctly"""
    adapter = Mock()
    ingest = DataIngestion(adapter, exchange_name="binance")
    assert ingest.adapter == adapter
    assert ingest.exchange_name == "binance"

@patch('trading_bot.data.ingestion.get_session')
def test_fetch_and_store_candles(mock_session):
    """Test candle fetching and storage"""
    adapter = Mock()
    adapter.fetch_market_data.return_value = [
        [1609459200000, 100.0, 105.0, 99.0, 104.0, 1000.0],
        [1609462800000, 104.0, 106.0, 103.0, 105.0, 1100.0]
    ]
    
    ingest = DataIngestion(adapter, exchange_name="binance")
    ingest.save_candles = Mock()  # Mock save method
    
    ingest.fetch_and_store_candles(["BTC/USDT"])
    adapter.fetch_market_data.assert_called()
    ingest.save_candles.assert_called()

@patch('trading_bot.data.ingestion.get_session')
def test_fetch_and_store_ticker(mock_session):
    """Test ticker fetching and storage"""
    adapter = Mock()
    adapter.fetch_ticker.return_value = {
        'last': 100.0,
        'bid': 99.5,
        'ask': 100.5
    }
    
    ingest = DataIngestion(adapter, exchange_name="binance")
    ingest.save_ticker = Mock()
    
    ingest.fetch_and_store_ticker(["BTC/USDT"])
    adapter.fetch_ticker.assert_called()
    ingest.save_ticker.assert_called()

def test_save_candles_ccxt_format():
    """Test saving candles in ccxt format"""
    adapter = Mock()
    ingest = DataIngestion(adapter, exchange_name="binance")
    
    # Mock ccxt format: [timestamp, open, high, low, close, volume]
    candles = [
        [1609459200000, 100.0, 105.0, 99.0, 104.0, 1000.0]
    ]
    
    with patch('trading_bot.data.ingestion.get_session') as mock_session:
        mock_session.return_value.__enter__.return_value.bulk_save_objects = Mock()
        ingest.save_candles("BTC/USDT", candles, "1m")
        mock_session.return_value.__enter__.return_value.bulk_save_objects.assert_called_once()

