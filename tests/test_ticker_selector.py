import pytest
from unittest.mock import patch
from stock_tool.ticker_selector import TickerSelector
from stock_tool.database_manager import DatabaseManager
from stock_tool.config_manager import ConfigManager

@pytest.fixture
def mock_db_manager():
    """Mock DatabaseManager with sample ticker data."""
    class MockDBManager:
        def query_data(self, sectors):
            all_tickers = [
                {'ticker': 'AAPL', 'sector': 'Technology', 'exchange': 'NASDAQ'},
                {'ticker': 'MSFT', 'sector': 'Technology', 'exchange': 'NASDAQ'},
                {'ticker': 'JNJ', 'sector': 'Healthcare', 'exchange': 'NYSE'},
                {'ticker': 'AMEX1', 'sector': 'Technology', 'exchange': 'AMEX'},
                {'ticker': 'AMEX2', 'sector': 'Healthcare', 'exchange': 'AMEX'}
            ]
            return [t for t in all_tickers if t['sector'] in sectors]

        def save_stock_data(self, ticker, data):
            pass  # Mock saving to database

    return MockDBManager()

@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager with a dummy API key."""
    class MockConfigManager:
        def get_fmp_api_key(self):
            return 'dummy_api_key'
    return MockConfigManager()

def test_get_tickers_with_cached_data(mock_db_manager, mock_config_manager):
    """Test selecting tickers from cache without API calls."""
    selector = TickerSelector(mock_db_manager, mock_config_manager)
    tickers = selector.get_tickers(2, ['Technology'], seed=42)
    assert len(tickers) == 2
    assert all(t in ['AAPL', 'MSFT', 'AMEX1'] for t in tickers)

def test_get_tickers_with_exchange_prioritization(mock_db_manager, mock_config_manager):
    """Test prioritizing tickers from a specified exchange."""
    selector = TickerSelector(mock_db_manager, mock_config_manager)
    tickers = selector.get_tickers(2, ['Technology'], exchange='AMEX', seed=42)
    assert len(tickers) == 2
    assert tickers[0] == 'AMEX1'
    assert tickers[1] in ['AAPL', 'MSFT']

def test_get_tickers_not_enough_cached(mock_db_manager, mock_config_manager):
    """Test fetching from API when cache is insufficient."""
    with patch.object(TickerSelector, 'fetch_tickers_from_api', return_value=[
        {'symbol': 'GOOGL', 'sector': 'Technology', 'exchange': 'NASDAQ'},
        {'symbol': 'AMZN', 'sector': 'Technology', 'exchange': 'NASDAQ'}
    ]):
        selector = TickerSelector(mock_db_manager, mock_config_manager)
        tickers = selector.get_tickers(5, ['Technology'], seed=42)
        assert len(tickers) == 5
        assert set(tickers).issubset({'AAPL', 'MSFT', 'AMEX1', 'GOOGL', 'AMZN'})

def test_get_tickers_reproducible(mock_db_manager, mock_config_manager):
    """Test that the same seed produces identical results."""
    selector = TickerSelector(mock_db_manager, mock_config_manager)
    tickers1 = selector.get_tickers(3, ['Technology'], seed=123)
    tickers2 = selector.get_tickers(3, ['Technology'], seed=123)
    assert tickers1 == tickers2

def test_get_tickers_more_than_available(mock_db_manager, mock_config_manager):
    """Test behavior when requesting more tickers than available."""
    with patch.object(TickerSelector, 'fetch_tickers_from_api', return_value=[]):
        selector = TickerSelector(mock_db_manager, mock_config_manager)
        tickers = selector.get_tickers(10, ['Technology'], seed=42)
        assert len(tickers) == 3  # Only 3 Technology tickers in mock data
        assert set(tickers) == {'AAPL', 'MSFT', 'AMEX1'}