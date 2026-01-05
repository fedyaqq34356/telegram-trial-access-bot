import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import contextmanager

class Database:
    def __init__(self, db_path: str = 'bot.db'):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    username TEXT,
                    join_date TEXT NOT NULL,
                    trial_end_date TEXT NOT NULL,
                    status TEXT DEFAULT 'trial',
                    in_work_chat INTEGER DEFAULT 1,
                    in_study_group INTEGER DEFAULT 1,
                    notified_one_day INTEGER DEFAULT 0
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    telegram_id INTEGER PRIMARY KEY
                )
            ''')
    
    def add_user(self, telegram_id: int, name: str, username: Optional[str], trial_minutes: int):
        join_date = datetime.now()
        trial_end = join_date + timedelta(minutes=trial_minutes)
        
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR IGNORE INTO users 
                (telegram_id, name, username, join_date, trial_end_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (telegram_id, name, username, join_date.isoformat(), trial_end.isoformat()))
    
    def get_user(self, telegram_id: int):
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM users WHERE telegram_id = ?',
                (telegram_id,)
            )
            return cursor.fetchone()
    
    def get_all_users(self) -> List[sqlite3.Row]:
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT * FROM users ORDER BY join_date DESC')
            return cursor.fetchall()
    
    def get_trial_users(self) -> List[sqlite3.Row]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE status = 'trial' ORDER BY trial_end_date"
            )
            return cursor.fetchall()
    
    def get_expired_trials(self) -> List[sqlite3.Row]:
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE status = 'trial' AND trial_end_date <= ?",
                (now,)
            )
            return cursor.fetchall()
    
    def get_users_expiring_soon(self, hours: int = 24) -> List[sqlite3.Row]:
        now = datetime.now()
        threshold = now + timedelta(hours=hours)
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM users 
                   WHERE status = 'trial' 
                   AND trial_end_date <= ? 
                   AND trial_end_date > ?
                   AND notified_one_day = 0""",
                (threshold.isoformat(), now.isoformat())
            )
            return cursor.fetchall()
    
    def mark_notified(self, telegram_id: int):
        with self._get_connection() as conn:
            conn.execute(
                'UPDATE users SET notified_one_day = 1 WHERE telegram_id = ?',
                (telegram_id,)
            )
    
    def update_status(self, telegram_id: int, status: str):
        with self._get_connection() as conn:
            conn.execute(
                'UPDATE users SET status = ? WHERE telegram_id = ?',
                (status, telegram_id)
            )
    
    def update_presence(self, telegram_id: int, in_work: bool, in_study: bool):
        with self._get_connection() as conn:
            conn.execute(
                'UPDATE users SET in_work_chat = ?, in_study_group = ? WHERE telegram_id = ?',
                (int(in_work), int(in_study), telegram_id)
            )
    
    def remove_user(self, telegram_id: int):
        with self._get_connection() as conn:
            conn.execute('DELETE FROM users WHERE telegram_id = ?', (telegram_id,))
    
    def add_admin(self, telegram_id: int):
        with self._get_connection() as conn:
            conn.execute('INSERT OR IGNORE INTO admins (telegram_id) VALUES (?)', (telegram_id,))
    
    def remove_admin(self, telegram_id: int):
        with self._get_connection() as conn:
            conn.execute('DELETE FROM admins WHERE telegram_id = ?', (telegram_id,))
    
    def get_all_admins(self) -> List[int]:
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT telegram_id FROM admins')
            return [row['telegram_id'] for row in cursor.fetchall()]
    
    def is_admin(self, telegram_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT telegram_id FROM admins WHERE telegram_id = ?',
                (telegram_id,)
            )
            return cursor.fetchone() is not None