import sqlite3
import time
from contextlib import closing
from config import config

def init_db():
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    join_date INTEGER,
                    last_active INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    country TEXT,
                    total_numbers INTEGER,
                    format_type TEXT,
                    file_name TEXT,
                    created_at INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('bot_active', '1')")

def get_bot_status():
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        cur = conn.execute("SELECT value FROM settings WHERE key='bot_active'")
        res = cur.fetchone()
        return res[0] == '1' if res else True

def set_bot_status(status: bool):
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        with conn:
            conn.execute("UPDATE settings SET value=? WHERE key='bot_active'", ('1' if status else '0',))

def add_or_update_user(user_id, username, first_name, last_name):
    now = int(time.time())
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        with conn:
            conn.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, join_date, last_active)
                VALUES (?,?,?,?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    last_name=excluded.last_name,
                    last_active=excluded.last_active
            """, (user_id, username, first_name, last_name, now, now))

def update_last_active(user_id):
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        with conn:
            conn.execute("UPDATE users SET last_active=? WHERE user_id=?", (int(time.time()), user_id))

def get_user(user_id):
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        cur = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return cur.fetchone()

def get_all_users():
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        cur = conn.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]

def get_total_users():
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]

def get_active_users(days=1):
    threshold = int(time.time()) - days * 86400
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM users WHERE last_active >?", (threshold,))
        return cur.fetchone()[0]

def save_file_record(user_id, country, total_numbers, format_type, file_name):
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        with conn:
            conn.execute("""
                INSERT INTO files (user_id, country, total_numbers, format_type, file_name, created_at)
                VALUES (?,?,?,?,?,?)
            """, (user_id, country, total_numbers, format_type, file_name, int(time.time())))

def get_user_files(user_id):
    with closing(sqlite3.connect(config.DB_NAME)) as conn:
        cur = conn.execute("""
            SELECT id, country, total_numbers, format_type, file_name, created_at
            FROM files WHERE user_id=? ORDER BY created_at DESC
        """, (user_id,))
        return cur.fetchall()
