import random
import requests
from typing import List, Optional
from .database_manager import DatabaseManager
from .config_manager import ConfigManager

class TickerSelector:
    def __init__(self, db_manager: DatabaseManager, config_manager: ConfigManager):
        self.db_manager = db_manager
        self.config_manager = config_manager

    def fetch_tickers_from_api(self, sectors: List[str], limit: int) -> List[dict]:
        """Fetch tickers from the FMP stock screener API."""
        api_key = self.config_manager.get_fmp_api_key()
        sectors_str = ','.join(sectors)
        url = f"https://financialmodelingprep.com/api/v3/stock-screener?sector={sectors_str}&limit={limit}&apikey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed with status {response.status_code}")

    def get_tickers(self, number_of_tickers: int, sectors: List[str], exchange: Optional[str] = None, seed: Optional[int] = None) -> List[str]:
        """Generate a list of tickers based on sectors, with optional exchange prioritization and randomization."""
        # Set random seed for reproducibility
        if seed is not None:
            random.seed(seed)

        # Ensure sectors is a list
        if isinstance(sectors, str):
            sectors = [sectors]

        # Query cached tickers from the database
        cached_tickers = self.db_manager.query_data(sectors=sectors)

        # Separate tickers into priority (specified exchange) and others
        if exchange:
            priority_tickers = [t for t in cached_tickers if t['exchange'] == exchange]
            other_tickers = [t for t in cached_tickers if t['exchange'] != exchange]
        else:
            priority_tickers = []
            other_tickers = cached_tickers

        # Shuffle for randomization
        random.shuffle(priority_tickers)
        random.shuffle(other_tickers)

        # Select tickers, prioritizing the specified exchange
        selected_tickers = [t['ticker'] for t in priority_tickers[:number_of_tickers]]
        remaining = number_of_tickers - len(selected_tickers)
        if remaining > 0:
            selected_tickers.extend([t['ticker'] for t in other_tickers[:remaining]])

        # Fetch from API if not enough tickers are cached
        if len(selected_tickers) < number_of_tickers:
            needed = number_of_tickers - len(selected_tickers)
            api_tickers = self.fetch_tickers_from_api(sectors, needed * 2)  # Fetch extra for flexibility
            # Cache new tickers
            for ticker_data in api_tickers:
                self.db_manager.save_stock_data(ticker_data['symbol'], {
                    'sector': ticker_data['sector'],
                    'exchange': ticker_data['exchange']
                })
            # Filter out already selected tickers
            api_tickers = [t for t in api_tickers if t['symbol'] not in selected_tickers]
            # Separate API tickers by exchange
            if exchange:
                api_priority = [t for t in api_tickers if t['exchange'] == exchange]
                api_other = [t for t in api_tickers if t['exchange'] != exchange]
            else:
                api_priority = []
                api_other = api_tickers
            # Shuffle API tickers
            random.shuffle(api_priority)
            random.shuffle(api_other)
            # Select from priority first
            selected_api = [t['symbol'] for t in api_priority[:needed]]
            remaining_api = needed - len(selected_api)
            if remaining_api > 0:
                selected_api.extend([t['symbol'] for t in api_other[:remaining_api]])
            selected_tickers.extend(selected_api)

        # Return the requested number of tickers
        return selected_tickers[:number_of_tickers]