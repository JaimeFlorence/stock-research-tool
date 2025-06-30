import pytest
from stock_tool.stock_analyzer import StockAnalyzer
from stock_tool.intrinsic_value_calculator import IntrinsicValueCalculator
from stock_tool.config_manager import ConfigManager
from unittest.mock import MagicMock

@pytest.fixture
def config_manager():
    test_config = {
        "sectors": {
            "Technology": {"growth_rate": 0.08, "pe_ratio": 25.0, "discount_rate": 0.10},
            "Healthcare": {"growth_rate": 0.06, "pe_ratio": 20.0, "discount_rate": 0.09}
        }
    }
    class TestConfigManager(ConfigManager):
        def __init__(self):
            self.config = test_config
    return TestConfigManager()

@pytest.fixture
def stock_data():
    return {
        'AAPL': {'price': 150.0, 'shares': 1_000_000_000, 'fcf': 10_000_000_000, 'sector': 'Technology', 'eps': 5.0},
        'MSFT': {'price': 200.0, 'shares': 750_000_000, 'fcf': None, 'sector': 'Technology', 'eps': 6.0},
        'TSLA': {'price': 250.0, 'shares': 3_000_000_000, 'fcf': 5_000_000_000, 'sector': 'Technology', 'eps': -1.0},
        'ZDGE': {'price': 10.0, 'shares': 10_000_000, 'fcf': 100_000_000, 'sector': 'Technology', 'eps': -0.5}
    }

@pytest.fixture
def analyzer(config_manager, stock_data):
    data_fetcher = MagicMock()
    data_fetcher.fetch_data.side_effect = lambda tickers: {ticker: stock_data[ticker] for ticker in tickers}
    intrinsic_value_calculator = IntrinsicValueCalculator(config_manager)
    return StockAnalyzer(data_fetcher, intrinsic_value_calculator)

def test_analyze_stocks_basic(analyzer):
    tickers = ['AAPL', 'MSFT', 'TSLA', 'ZDGE']
    filter_params = {'max_pe': 30, 'exclude_negative_pe': True}
    result = analyzer.analyze_stocks(tickers, filter_params)
    assert len(result) == 2
    assert result[0]['ticker'] == 'ZDGE'
    assert result[0]['score'] == pytest.approx(19.665, rel=0.01)  # Updated value

def test_analyze_stocks_no_filters(analyzer):
    tickers = ['AAPL', 'MSFT', 'TSLA', 'ZDGE']
    filter_params = {}
    result = analyzer.analyze_stocks(tickers, filter_params)
    assert len(result) == 4
    assert result[0]['ticker'] == 'ZDGE'
    assert result[1]['ticker'] == 'AAPL'
    assert result[2]['ticker'] == 'MSFT'
    assert result[3]['ticker'] == 'TSLA'

def test_analyze_stocks_sector_grouping(analyzer):
    tickers = ['AAPL', 'MSFT', 'TSLA', 'ZDGE']
    filter_params = {'max_pe': 30, 'exclude_negative_pe': True}
    sector_prefs = ['Technology']
    result = analyzer.analyze_stocks(tickers, filter_params, sector_prefs)
    assert 'Technology' in result
    assert len(result['Technology']) == 2
    assert result['Technology'][0]['ticker'] == 'ZDGE'
    assert result['Technology'][1]['ticker'] == 'AAPL'

def test_analyze_stocks_no_passing(analyzer):
    tickers = ['TSLA']
    filter_params = {'exclude_negative_pe': True}
    result = analyzer.analyze_stocks(tickers, filter_params)
    assert len(result) == 0

def test_analyze_stocks_amex_negative_eps(analyzer):
    tickers = ['ZDGE']
    filter_params = {'exclude_negative_pe': True}
    result = analyzer.analyze_stocks(tickers, filter_params)
    assert len(result) == 1
    assert result[0]['ticker'] == 'ZDGE'