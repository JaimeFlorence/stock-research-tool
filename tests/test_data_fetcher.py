import pytest
import logging
from freezegun import freeze_time
import requests_mock
from stock_tool.data_fetcher import DataFetcher, APIKeyNotFoundError
from stock_tool.database_manager import DatabaseManager
from stock_tool.config_manager import ConfigManager

# Ensure logging is captured
logging.getLogger('').setLevel(logging.INFO)

@pytest.fixture
def db_manager():
    """Fixture to create a DatabaseManager instance with an in-memory database."""
    return DatabaseManager(db_path=':memory:')

@pytest.fixture
def fetcher(db_manager):
    """Fixture to create a DataFetcher instance with a dummy API key and DatabaseManager."""
    return DataFetcher(db_manager=db_manager, api_key='dummy_key')

def test_fetch_data_happy_path(fetcher, requests_mock):
    """Test fetching data for a single ticker with all required fields present."""
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/quote/AAPL?apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'price': 150.0}]
    )
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/profile/AAPL?apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'sharesOutstanding': 1000000, 'sector': 'Technology'}]
    )
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/cash-flow-statement/AAPL?period=annual&limit=1&apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'freeCashFlow': 1000000}]
    )
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&limit=1&apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'eps': 5.0}]
    )

    data = fetcher.fetch_data('AAPL')
    assert data == {'AAPL': {'price': 150.0, 'shares': 1000000, 'fcf': 1000000, 'sector': 'Technology', 'eps': 5.0}}

    cached_data = fetcher.db_manager.get_cached_data('AAPL')
    assert cached_data['price'] == 150.0
    assert cached_data['shares'] == 1000000
    assert cached_data['fcf'] == 1000000
    assert cached_data['sector'] == 'Technology'
    assert cached_data['eps'] == 5.0
    assert cached_data['intrinsic_value'] is None
    assert cached_data['score'] is None

def test_caching(fetcher, requests_mock):
    """Test that fetching data twice uses the cache on the second fetch."""
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/quote/AAPL?apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'price': 150.0}]
    )
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/profile/AAPL?apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'sharesOutstanding': 1000000, 'sector': 'Technology'}]
    )
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/cash-flow-statement/AAPL?period=annual&limit=1&apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'freeCashFlow': 1000000}]
    )
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&limit=1&apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'eps': 5.0}]
    )

    data1 = fetcher.fetch_data('AAPL')
    expected_data = {'price': 150.0, 'shares': 1000000, 'fcf': 1000000, 'sector': 'Technology', 'eps': 5.0}
    assert data1 == {'AAPL': expected_data}
    assert requests_mock.call_count == 4

    data2 = fetcher.fetch_data('AAPL')
    assert data2 == {'AAPL': expected_data}
    assert requests_mock.call_count == 4

def test_cache_expiration():
    """Test that cache expires after the specified duration."""
    with freeze_time("2023-01-01 00:00:00"):
        db_manager = DatabaseManager(db_path=':memory:')
        fetcher = DataFetcher(db_manager=db_manager, api_key='dummy_key', cache_duration_days=1e-5)
        with requests_mock.Mocker() as m:
            m.get(
                'https://financialmodelingprep.com/api/v3/quote/AAPL?apikey=dummy_key',
                json=[{'symbol': 'AAPL', 'price': 150.0}]
            )
            m.get(
                'https://financialmodelingprep.com/api/v3/profile/AAPL?apikey=dummy_key',
                json=[{'symbol': 'AAPL', 'sharesOutstanding': 1000000, 'sector': 'Technology'}]
            )
            m.get(
                'https://financialmodelingprep.com/api/v3/cash-flow-statement/AAPL?period=annual&limit=1&apikey=dummy_key',
                json=[{'symbol': 'AAPL', 'freeCashFlow': 1000000}]
            )
            m.get(
                'https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&limit=1&apikey=dummy_key',
                json=[{'symbol': 'AAPL', 'eps': 5.0}]
            )
            data1 = fetcher.fetch_data('AAPL')
            expected_data = {'price': 150.0, 'shares': 1000000, 'fcf': 1000000, 'sector': 'Technology', 'eps': 5.0}
            assert data1 == {'AAPL': expected_data}
            assert m.call_count == 4

    with freeze_time("2023-01-01 00:00:01"):
        with requests_mock.Mocker() as m:
            m.get(
                'https://financialmodelingprep.com/api/v3/quote/AAPL?apikey=dummy_key',
                json=[{'symbol': 'AAPL', 'price': 150.0}]
            )
            m.get(
                'https://financialmodelingprep.com/api/v3/profile/AAPL?apikey=dummy_key',
                json=[{'symbol': 'AAPL', 'sharesOutstanding': 1000000, 'sector': 'Technology'}]
            )
            m.get(
                'https://financialmodelingprep.com/api/v3/cash-flow-statement/AAPL?period=annual&limit=1&apikey=dummy_key',
                json=[{'symbol': 'AAPL', 'freeCashFlow': 1000000}]
            )
            m.get(
                'https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&limit=1&apikey=dummy_key',
                json=[{'symbol': 'AAPL', 'eps': 5.0}]
            )
            data2 = fetcher.fetch_data('AAPL')
            assert data2 == {'AAPL': expected_data}
            assert m.call_count == 4

def test_incomplete_data(fetcher, requests_mock, caplog):
    """Test handling of incomplete data from API."""
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/quote/AAPL?apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'price': 150.0}]
    )
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/profile/AAPL?apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'sharesOutstanding': 1000000, 'sector': 'Technology'}]
    )
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/cash-flow-statement/AAPL?period=annual&limit=1&apikey=dummy_key',
        json=[{'symbol': 'AAPL'}]
    )
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&limit=1&apikey=dummy_key',
        json=[{'symbol': 'AAPL', 'eps': 5.0}]
    )

    with caplog.at_level(logging.INFO):
        data = fetcher.fetch_data('AAPL')
        assert data == {}
        assert "Missing required fields for AAPL: ['fcf']" in caplog.text

    cached_data = fetcher.db_manager.get_cached_data('AAPL')
    assert cached_data is None

def test_api_error(fetcher, requests_mock, caplog):
    """Test handling of API errors."""
    requests_mock.get(
        'https://financialmodelingprep.com/api/v3/quote/AAPL?apikey=dummy_key',
        status_code=404, reason='Not Found'
    )

    with caplog.at_level(logging.INFO):
        data = fetcher.fetch_data('AAPL')
        assert data == {}
        assert "Error fetching data for AAPL: 404 Client Error: Not Found" in caplog.text

    cached_data = fetcher.db_manager.get_cached_data('AAPL')
    assert cached_data is None

def test_multiple_tickers(fetcher, requests_mock):
    """Test fetching data for multiple tickers."""
    for ticker in ['AAPL', 'MSFT']:
        requests_mock.get(
            f'https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey=dummy_key',
            json=[{'symbol': ticker, 'price': 150.0 if ticker == 'AAPL' else 250.0}]
        )
        requests_mock.get(
            f'https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey=dummy_key',
            json=[{'symbol': ticker, 'sharesOutstanding': 1000000 if ticker == 'AAPL' else 2000000, 'sector': 'Technology'}]
        )
        requests_mock.get(
            f'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit=1&apikey=dummy_key',
            json=[{'symbol': ticker, 'freeCashFlow': 1000000 if ticker == 'AAPL' else 2000000}]
        )
        requests_mock.get(
            f'https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=annual&limit=1&apikey=dummy_key',
            json=[{'symbol': ticker, 'eps': 5.0 if ticker == 'AAPL' else 10.0}]
        )

    data = fetcher.fetch_data(['AAPL', 'MSFT'])
    assert data == {
        'AAPL': {'price': 150.0, 'shares': 1000000, 'fcf': 1000000, 'sector': 'Technology', 'eps': 5.0},
        'MSFT': {'price': 250.0, 'shares': 2000000, 'fcf': 2000000, 'sector': 'Technology', 'eps': 10.0}
    }

def test_api_key_from_config(db_manager, monkeypatch):
    """Test that DataFetcher retrieves API key from ConfigManager."""
    monkeypatch.setenv("FMP_API_Key", "test_api_key")
    fetcher = DataFetcher(db_manager=db_manager)