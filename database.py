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
                    in_work_chat INTEGER DEFAULT 0,
                    in_study_group INTEGER DEFAULT 0,
                    notified_one_day INTEGER DEFAULT 0
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    telegram_id INTEGER PRIMARY KEY
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS check_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id INTEGER,
                    username TEXT,
                    anchor_id TEXT,
                    agency TEXT,
                    down_rate TEXT,
                    real_down_rate TEXT,
                    monthly_income TEXT,
                    grade TEXT,
                    has_risk INTEGER DEFAULT 0,
                    found INTEGER DEFAULT 0,
                    created_at TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL DEFAULT 'https://admin.livegirl.me',
                    account TEXT NOT NULL,
                    password TEXT NOT NULL,
                    aemail TEXT NOT NULL,
                    apassword TEXT NOT NULL,
                    tfa_required INTEGER DEFAULT 0
                )
            ''')
            cursor = conn.execute('SELECT COUNT(*) FROM agencies')
            if cursor.fetchone()[0] == 0:
                try:
                    from agencies import AGENCIES
                    for ag in AGENCIES:
                        conn.execute('''
                            INSERT INTO agencies (name, url, account, password, aemail, apassword, tfa_required)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (ag['name'], ag['url'], ag['account'], ag['password'],
                              ag['aemail'], ag['apassword'], int(ag.get('tfa_required', False))))
                except Exception:
                    pass
    
    def add_user(self, telegram_id: int, name: str, username: Optional[str], trial_minutes: int):
        join_date = datetime.now()
        trial_end = join_date + timedelta(minutes=trial_minutes)
        
        with self._get_connection() as conn:
            # ВАЖНО: По умолчанию пользователь НЕ находится ни в одном чате
            # Флаги будут установлены отдельно через update_presence
            conn.execute('''
                INSERT OR IGNORE INTO users 
                (telegram_id, name, username, join_date, trial_end_date, in_work_chat, in_study_group)
                VALUES (?, ?, ?, ?, ?, 0, 0)
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
        """Обновляет флаги присутствия пользователя в чатах"""
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

    def save_check(self, tg_id, username, anchor_id, agency, down_rate,
                   real_down_rate, monthly_income, grade, has_risk, found):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO check_history
                (tg_id, username, anchor_id, agency, down_rate, real_down_rate,
                 monthly_income, grade, has_risk, found, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tg_id, username, anchor_id, agency, str(down_rate), str(real_down_rate),
                  str(monthly_income), grade, int(has_risk), int(found),
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    def get_history(self, limit: int = 20):
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM check_history ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            return cursor.fetchall()

    def get_all_agencies(self):
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT * FROM agencies ORDER BY id')
            return cursor.fetchall()

    def get_agency(self, agency_id: int):
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT * FROM agencies WHERE id = ?', (agency_id,))
            return cursor.fetchone()

    def add_agency(self, name, url, account, password, aemail, apassword, tfa_required):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO agencies (name, url, account, password, aemail, apassword, tfa_required)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, url, account, password, aemail, apassword, int(tfa_required)))

    def remove_agency(self, agency_id: int):
        with self._get_connection() as conn:
            conn.execute('DELETE FROM agencies WHERE id = ?', (agency_id,))

    def update_agency(self, agency_id: int, field: str, value):
        allowed = {"name", "account", "password", "aemail", "apassword", "tfa_required"}
        if field not in allowed:
            raise ValueError(f"Invalid field: {field}")
        with self._get_connection() as conn:
            conn.execute(f'UPDATE agencies SET {field} = ? WHERE id = ?', (value, agency_id))
