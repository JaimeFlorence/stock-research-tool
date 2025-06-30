import sqlite3
from datetime import datetime, timedelta, timezone

class DatabaseManager:
    """
    A class to manage SQLite database operations for the stock research tool.
    """
    def __init__(self, db_path='stock_data.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_db()

    def create_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                ticker TEXT PRIMARY KEY,
                price REAL,
                shares REAL,
                fcf REAL,
                sector TEXT,
                eps REAL,
                intrinsic_value REAL,
                score REAL,
                timestamp TEXT
            )
        ''')
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sector ON stock_data (sector)")
        self.conn.commit()

    def save_stock_data(self, ticker, data):
        cursor = self.conn.cursor()
        price = data.get('price')
        shares = data.get('shares')
        fcf = data.get('fcf')
        sector = data.get('sector')
        eps = data.get('eps')
        timestamp = datetime.now(timezone.utc).isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO stock_data (ticker, price, shares, fcf, sector, eps, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ticker, price, shares, fcf, sector, eps, timestamp))
        self.conn.commit()

    def save_intrinsic_value(self, ticker, value):
        cursor = self.conn.cursor()
        timestamp = datetime.now(timezone.utc).isoformat()
        cursor.execute('''
            UPDATE stock_data SET intrinsic_value = ?, timestamp = ? WHERE ticker = ?
        ''', (value, timestamp, ticker))
        self.conn.commit()

    def save_score(self, ticker, score):
        cursor = self.conn.cursor()
        timestamp = datetime.now(timezone.utc).isoformat()
        cursor.execute('''
            UPDATE stock_data SET score = ?, timestamp = ? WHERE ticker = ?
        ''', (score, timestamp, ticker))
        self.conn.commit()

    def query_data(self, **kwargs):
        conditions = []
        params = []
        if 'tickers' in kwargs:
            tickers = kwargs['tickers']
            if isinstance(tickers, str):
                conditions.append("ticker = ?")
                params.append(tickers)
            else:
                conditions.append("ticker IN (" + ",".join("?" * len(tickers)) + ")")
                params.extend(tickers)
        if 'sectors' in kwargs:
            sectors = kwargs['sectors']
            if isinstance(sectors, str):
                conditions.append("sector = ?")
                params.append(sectors)
            else:
                conditions.append("sector IN (" + ",".join("?" * len(sectors)) + ")")
                params.extend(sectors)
        if 'min_fcf' in kwargs:
            conditions.append("fcf >= ?")
            params.append(kwargs['min_fcf'])

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM stock_data WHERE {where_clause}"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def clear_outdated_data(self, days):
        cursor = self.conn.cursor()
        cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).isoformat()
        cursor.execute("DELETE FROM stock_data WHERE timestamp < ?", (cutoff,))
        self.conn.commit()

    def get_cached_data(self, ticker):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM stock_data WHERE ticker = ?", (ticker,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

    def close(self):
        self.conn.close()