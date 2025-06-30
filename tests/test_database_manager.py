import pytest
from datetime import datetime, timezone
from freezegun import freeze_time
from stock_tool.database_manager import DatabaseManager

@pytest.fixture
def db_manager():
    """Fixture to create a DatabaseManager instance with an in-memory database."""
    db = DatabaseManager(db_path=':memory:')
    yield db
    db.close()

def test_create_db(db_manager):
    """Test that the database schema is created correctly."""
    cursor = db_manager.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_data'")
    assert cursor.fetchone() is not None, "Table 'stock_data' should be created."
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_sector'")
    assert cursor.fetchone() is not None, "Index 'idx_sector' should be created."

def test_save_stock_data_insert(db_manager):
    """Test inserting new stock data."""
    data = {'price': 100.0, 'shares': 1000000, 'fcf': 500000, 'sector': 'Tech', 'eps': 5.0}
    db_manager.save_stock_data('AAPL', data)
    cursor = db_manager.conn.cursor()
    cursor.execute("SELECT * FROM stock_data WHERE ticker='AAPL'")
    row = cursor.fetchone()
    assert row is not None, "Data should be inserted."
    assert row[1] == 100.0, "Price should be 100.0."
    assert row[2] == 1000000, "Shares should be 1000000."
    assert row[3] == 500000, "FCF should be 500000."
    assert row[4] == 'Tech', "Sector should be 'Tech'."
    assert row[5] == 5.0, "EPS should be 5.0."

def test_save_stock_data_update(db_manager):
    """Test updating existing stock data."""
    data1 = {'price': 100.0, 'shares': 1000000, 'fcf': 500000, 'sector': 'Tech', 'eps': 5.0}
    db_manager.save_stock_data('AAPL', data1)
    data2 = {'price': 150.0, 'shares': 1000000, 'fcf': 600000, 'sector': 'Tech', 'eps': 6.0}
    db_manager.save_stock_data('AAPL', data2)
    cursor = db_manager.conn.cursor()
    cursor.execute("SELECT * FROM stock_data WHERE ticker='AAPL'")
    row = cursor.fetchone()
    assert row[1] == 150.0, "Price should be updated to 150.0."
    assert row[3] == 600000, "FCF should be updated to 600000."
    assert row[5] == 6.0, "EPS should be updated to 6.0."

def test_save_intrinsic_value(db_manager):
    """Test updating intrinsic value."""
    data = {'price': 100.0}
    db_manager.save_stock_data('AAPL', data)
    db_manager.save_intrinsic_value('AAPL', 120.0)
    cached_data = db_manager.get_cached_data('AAPL')
    assert cached_data['intrinsic_value'] == 120.0, "Intrinsic value should be 120.0."

def test_save_score(db_manager):
    """Test updating score."""
    data = {'price': 100.0}
    db_manager.save_stock_data('AAPL', data)
    db_manager.save_score('AAPL', 85.0)
    cached_data = db_manager.get_cached_data('AAPL')
    assert cached_data['score'] == 85.0, "Score should be 85.0."

def test_query_data_by_ticker(db_manager):
    """Test querying data by ticker."""
    data1 = {'price': 100.0, 'sector': 'Tech'}
    data2 = {'price': 200.0, 'sector': 'Finance'}
    db_manager.save_stock_data('AAPL', data1)
    db_manager.save_stock_data('MSFT', data2)
    result = db_manager.query_data(tickers='AAPL')
    assert len(result) == 1, "Should return one result."
    assert result[0]['ticker'] == 'AAPL', "Ticker should be 'AAPL'."
    assert result[0]['price'] == 100.0, "Price should be 100.0."

def test_query_data_by_sector(db_manager):
    """Test querying data by sector."""
    data1 = {'price': 100.0, 'sector': 'Tech'}
    data2 = {'price': 200.0, 'sector': 'Tech'}
    data3 = {'price': 300.0, 'sector': 'Finance'}
    db_manager.save_stock_data('AAPL', data1)
    db_manager.save_stock_data('MSFT', data2)
    db_manager.save_stock_data('JPM', data3)
    result = db_manager.query_data(sectors='Tech')
    assert len(result) == 2, "Should return two results."
    tickers = {r['ticker'] for r in result}
    assert tickers == {'AAPL', 'MSFT'}, "Should return 'AAPL' and 'MSFT'."

def test_query_data_by_criteria(db_manager):
    """Test querying data with multiple criteria."""
    data1 = {'price': 100.0, 'sector': 'Tech', 'fcf': 500000}
    data2 = {'price': 200.0, 'sector': 'Tech', 'fcf': 1000000}
    data3 = {'price': 300.0, 'sector': 'Finance', 'fcf': 1500000}
    db_manager.save_stock_data('AAPL', data1)
    db_manager.save_stock_data('MSFT', data2)
    db_manager.save_stock_data('JPM', data3)
    result = db_manager.query_data(sectors='Tech', min_fcf=700000)
    assert len(result) == 1, "Should return one result."
    assert result[0]['ticker'] == 'MSFT', "Ticker should be 'MSFT'."

def test_clear_outdated_data(db_manager):
    """Test clearing outdated data."""
    with freeze_time("2022-12-01"):
        db_manager.save_stock_data('AAPL', {'price': 100.0})
    with freeze_time("2022-12-15"):
        db_manager.save_stock_data('MSFT', {'price': 200.0})
    with freeze_time("2022-12-30"):
        db_manager.clear_outdated_data(days=15)
    cursor = db_manager.conn.cursor()
    cursor.execute("SELECT * FROM stock_data")
    rows = cursor.fetchall()
    assert len(rows) == 1, "Only one row should remain."
    assert rows[0][0] == 'MSFT', "Remaining ticker should be 'MSFT'."

def test_get_cached_data(db_manager):
    """Test retrieving cached data."""
    data = {'price': 100.0, 'shares': 1000000, 'fcf': 500000, 'sector': 'Tech', 'eps': 5.0}
    db_manager.save_stock_data('AAPL', data)
    cached = db_manager.get_cached_data('AAPL')
    assert cached is not None, "Cached data should be retrieved."
    assert cached['price'] == 100.0, "Price should be 100.0."
    assert cached['sector'] == 'Tech', "Sector should be 'Tech'."

def test_query_data_no_results(db_manager):
    """Test querying with no matching results."""
    result = db_manager.query_data(tickers='NONEXISTENT')
    assert len(result) == 0, "Should return no results."

def test_close(db_manager):
    """Test closing the database connection."""
    db_manager.close()