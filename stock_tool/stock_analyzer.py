from typing import List, Dict, Optional
from .data_fetcher import DataFetcher
from .intrinsic_value_calculator import IntrinsicValueCalculator

class StockAnalyzer:
    """
    A class to analyze stocks by fetching data, calculating intrinsic values, applying filters,
    scoring stocks, and ranking them based on intrinsic-to-price ratios.
    """
    AMEX_TICKERS = {'ZDGE', 'SGE', 'WTT', 'LGL'}  # Example AMEX tickers; adjust as needed

    def __init__(self, data_fetcher: DataFetcher, intrinsic_value_calculator: IntrinsicValueCalculator):
        """
        Initialize the StockAnalyzer with instances of DataFetcher and IntrinsicValueCalculator.
        """
        self.data_fetcher = data_fetcher
        self.intrinsic_value_calculator = intrinsic_value_calculator

    def analyze_stocks(self, tickers: List[str], filter_params: Dict[str, any], sector_prefs: Optional[List[str]] = None) -> List[Dict[str, any]] | Dict[str, List[Dict[str, any]]]:
        """
        Analyze a list of stock tickers, applying filters and calculating scores based on intrinsic value.

        Args:
            tickers (List[str]): List of stock tickers to analyze.
            filter_params (Dict[str, any]): Dictionary of filter parameters (e.g., 'max_pe', 'exclude_negative_pe').
            sector_prefs (Optional[List[str]]): Optional list of sectors to group and rank stocks by.

        Returns:
            List[Dict[str, any]] | Dict[str, List[Dict[str, any]]]: Ranked list of stocks or dictionary of ranked lists by sector.
        """
        # Fetch stock data
        stock_data = self.data_fetcher.fetch_data(tickers)

        # Prepare stock list with additional calculated fields
        stock_list = []
        for ticker, data in stock_data.items():
            data['ticker'] = ticker
            if data.get('eps', 0) > 0:
                data['pe_ratio'] = data['price'] / data['eps']
            else:
                data['pe_ratio'] = float('-inf')
            stock_list.append(data)

        # Calculate intrinsic values
        for stock in stock_list:
            intrinsic_value = self.intrinsic_value_calculator.get_intrinsic_value(stock)
            stock['intrinsic_value'] = intrinsic_value

        # Apply filters
        filtered_stocks = [stock for stock in stock_list if self.passes_filters(stock, filter_params)]

        # Calculate scores
        for stock in filtered_stocks:
            if stock['price'] > 0:
                stock['score'] = stock['intrinsic_value'] / stock['price']
            else:
                stock['score'] = 0

        # Prepare output with selected metrics
        output_stocks = [
            {
                'ticker': stock['ticker'],
                'score': stock['score'],
                'intrinsic_value': stock['intrinsic_value'],
                'price': stock['price'],
                'sector': stock['sector']
            }
            for stock in filtered_stocks
        ]

        # Group and rank by sector if sector_prefs is provided
        if sector_prefs:
            grouped = {sector: [] for sector in sector_prefs}
            for stock in output_stocks:
                sector = stock['sector']
                if sector in grouped:
                    grouped[sector].append(stock)
            for sector, stocks in grouped.items():
                grouped[sector] = sorted(stocks, key=lambda x: x['score'], reverse=True)
            return grouped
        else:
            # Rank overall
            ranked_stocks = sorted(output_stocks, key=lambda x: x['score'], reverse=True)
            return ranked_stocks

    def passes_filters(self, stock: Dict[str, any], filter_params: Dict[str, any]) -> bool:
        """
        Check if a stock passes the specified filters.

        Args:
            stock (Dict[str, any]): Stock data dictionary.
            filter_params (Dict[str, any]): Filter parameters.

        Returns:
            bool: True if the stock passes all filters, False otherwise.
        """
        if stock['intrinsic_value'] is None or stock['intrinsic_value'] <= 0:
            return False
        if filter_params.get('exclude_negative_pe', False):
            if stock['ticker'] not in self.AMEX_TICKERS and stock['pe_ratio'] <= 0:
                return False
        if 'max_pe' in filter_params and stock['pe_ratio'] > filter_params['max_pe']:
            return False
        # Add other filters as needed
        return True