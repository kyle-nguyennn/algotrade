
import sqlite3

def ensure_schema(path: str):
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS fills(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy_id TEXT,
        dt TEXT,
        symbol TEXT,
        side TEXT,
        qty INTEGER,
        price REAL,
        commission REAL
    )
    ''')
    con.commit()
    con.close()

def insert_fill(path: str, fill: dict):
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute(
        'INSERT INTO fills(strategy_id, dt, symbol, side, qty, price, commission) VALUES(?,?,?,?,?,?,?)',
        (fill["strategy_id"], fill["dt"], fill["symbol"], fill["side"], fill["qty"], fill["price"], fill["commission"])
    )
    con.commit()
    con.close()
