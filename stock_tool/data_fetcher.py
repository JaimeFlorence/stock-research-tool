import requests
import logging
from datetime import datetime, timedelta, timezone
from .database_manager import DatabaseManager
from .config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIKeyNotFoundError(Exception):
    """Exception raised when the FMP API key is not found in the configuration."""
    pass

class DataFetcher:
    """
    A class to fetch stock data from the FMP API and manage caching via DatabaseManager.
    """
    def __init__(self, db_manager: DatabaseManager, api_key: str = None, cache_duration_days: int = 1):
        if api_key is None:
            api_key = self.get_fmp_api_key()
        self.api_key = api_key
        self.db_manager = db_manager
        self.cache_duration = timedelta(days=cache_duration_days)

    @staticmethod
    def get_fmp_api_key():
        """
        Retrieves the FMP API key from the ConfigManager.
        """
        config_manager = ConfigManager()
        api_key = config_manager.get_fmp_api_key()
        if api_key is None:
            raise APIKeyNotFoundError("FMP API key not found in configuration.")
        return api_key

    def fetch_data(self, tickers, required_fields=['price', 'shares', 'fcf'], use_cache=True):
        """
        Fetches stock data for the given ticker(s), using cache if available and valid.
        """
        if isinstance(tickers, str):
            tickers = [tickers]

        result = {}
        to_fetch = []

        if use_cache:
            for ticker in tickers:
                cached_data = self.db_manager.get_cached_data(ticker)
                if (cached_data and
                    all(cached_data.get(field) is not None for field in required_fields) and
                    self.is_cache_valid(cached_data['timestamp'])):
                    result[ticker] = {
                        'price': cached_data['price'],
                        'shares': cached_data['shares'],
                        'fcf': cached_data['fcf'],
                        'sector': cached_data['sector'],
                        'eps': cached_data['eps']
                    }
                else:
                    to_fetch.append(ticker)
        else:
            to_fetch = tickers

        if to_fetch:
            api_data = self.fetch_from_api(to_fetch)
            for ticker, data in api_data.items():
                if self.validate_data(data, required_fields):
                    self.db_manager.save_stock_data(ticker, data)
                    result[ticker] = data
                else:
                    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
                    logger.info(f"Missing required fields for {ticker}: {missing_fields}")

        return result

    def is_cache_valid(self, timestamp_str):
        """
        Checks if the cached data is still valid based on the cache duration.
        """
        timestamp = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - timestamp < self.cache_duration

    def fetch_from_api(self, tickers):
        """
        Fetches stock data from the FMP API for the given tickers.
        """
        result = {}
        for ticker in tickers:
            try:
                price_response = requests.get(f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={self.api_key}")
                price_response.raise_for_status()
                price_data = price_response.json()
                price = price_data[0]['price'] if price_data and 'price' in price_data[0] else None

                profile_response = requests.get(f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={self.api_key}")
                profile_response.raise_for_status()
                profile_data = profile_response.json()
                shares = profile_data[0]['sharesOutstanding'] if profile_data and 'sharesOutstanding' in profile_data[0] else None
                sector = profile_data[0]['sector'] if profile_data and 'sector' in profile_data[0] else None

                cashflow_response = requests.get(f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit=1&apikey={self.api_key}")
                cashflow_response.raise_for_status()
                cashflow_data = cashflow_response.json()
                fcf = cashflow_data[0]['freeCashFlow'] if cashflow_data and 'freeCashFlow' in cashflow_data[0] else None

                income_response = requests.get(f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=annual&limit=1&apikey={self.api_key}")
                income_response.raise_for_status()
                income_data = income_response.json()
                eps = income_data[0]['eps'] if income_data and 'eps' in income_data[0] else None

                data = {
                    'price': price,
                    'shares': shares,
                    'fcf': fcf,
                    'sector': sector,
                    'eps': eps
                }
                result[ticker] = data
            except (requests.exceptions.RequestException, IndexError, KeyError) as e:
                logger.info(f"Error fetching data for {ticker}: {e}")
        return result

    def validate_data(self, data, required_fields):
        """
        Validates that the data contains all required fields with non-None values.
        """
        return all(field in data and data[field] is not None for field in required_fields)