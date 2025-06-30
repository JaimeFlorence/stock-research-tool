import pytest
from stock_tool.intrinsic_value_calculator import IntrinsicValueCalculator
from stock_tool.config_manager import ConfigManager

@pytest.fixture
def config_manager():
    """Fixture providing a ConfigManager with test sector defaults."""
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

def test_complete_data(config_manager):
    """Test intrinsic value calculation with all data available."""
    calculator = IntrinsicValueCalculator(config_manager)
    stock_data = {
        'ticker': 'AAPL',
        'price': 150.0,
        'shares': 1_000_000_000,
        'fcf': 10_000_000_000,
        'sector': 'Technology',
        'eps': 5.0,
        'growth_rate': 0.10,
        'fmp_dcf': 160.0
    }
    value = calculator.get_intrinsic_value(stock_data)
    # PEG: 25 * (0.10 / 0.08) * 5 = 156.25
    # DCF: ~227.59
    # Expected: (227.59 + 156.25 + 160) / 3 ≈ 181.28
    assert value == pytest.approx(181.28, rel=0.05)

def test_missing_fcf(config_manager):
    """Test calculation when FCF is missing."""
    calculator = IntrinsicValueCalculator(config_manager)
    stock_data = {
        'ticker': 'MSFT',
        'price': 200.0,
        'shares': 750_000_000,
        'fcf': None,
        'sector': 'Technology',
        'eps': 6.0,
        'growth_rate': 0.12,
        'fmp_dcf': 180.0
    }
    value = calculator.get_intrinsic_value(stock_data)
    # PEG: 25 * (0.12 / 0.08) * 6 = 225
    # Expected: (225 + 180) / 2 = 202.5
    assert value == 202.5

def test_negative_eps(config_manager):
    """Test calculation with negative EPS."""
    calculator = IntrinsicValueCalculator(config_manager)
    stock_data = {
        'ticker': 'TSLA',
        'price': 250.0,
        'shares': 3_000_000_000,
        'fcf': 5_000_000_000,
        'sector': 'Technology',
        'eps': -1.0,
        'growth_rate': 0.15,
        'fmp_dcf': 200.0
    }
    value = calculator.get_intrinsic_value(stock_data)
    # DCF: ~54.29
    # PEG: Not calculated (negative EPS)
    # Expected: (54.29 + 200) / 2 ≈ 127.15
    assert value == pytest.approx(127.15, rel=0.05)

def test_missing_growth_rate(config_manager):
    """Test using sector default growth rate."""
    calculator = IntrinsicValueCalculator(config_manager)
    stock_data = {
        'ticker': 'GOOGL',
        'price': 1800.0,
        'shares': 300_000_000,
        'fcf': 60_000_000_000,
        'sector': 'Technology',
        'eps': 50.0,
        'fmp_dcf': 1900.0
    }
    value = calculator.get_intrinsic_value(stock_data)
    # PEG: 25 * (0.08 / 0.08) * 50 = 1250
    # DCF: ~3922.47
    # Expected: (3922.47 + 1250 + 1900) / 3 ≈ 2357.49
    assert value == pytest.approx(2357.49, rel=0.05)

def test_no_calculable_values(config_manager):
    """Test when no intrinsic values can be calculated."""
    calculator = IntrinsicValueCalculator(config_manager)
    stock_data = {
        'ticker': 'XYZ',
        'price': 100.0,
        'shares': 0,
        'fcf': None,
        'sector': 'Technology',
        'eps': -1.0
    }
    value = calculator.get_intrinsic_value(stock_data)
    assert value is None