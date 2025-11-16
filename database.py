import sqlite3
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='fitness_pro.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Пользователи
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                goals TEXT,
                fitness_level TEXT DEFAULT 'beginner',
                preferred_time TEXT DEFAULT '18:00',
                subscription_type TEXT DEFAULT 'trial',
                subscription_end DATE,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                workout_count INTEGER DEFAULT 0,
                last_workout DATE,
                total_calories INTEGER DEFAULT 0,
                conversation_history TEXT DEFAULT '[]'
            )
        ''')

        # Лиды и продажи
        cur.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stage TEXT DEFAULT 'new',
                interest_level INTEGER DEFAULT 1,
                last_contact DATE,
                next_contact DATE,
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✅ Профессиональная БД создана")

    def add_user(self, user_id, username, first_name, last_name):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        trial_end = datetime.now() + timedelta(days=7)

        cur.execute('''
            INSERT OR IGNORE INTO users
            (user_id, username, first_name, last_name, subscription_end)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, trial_end.date()))

        # Добавляем в лиды
        cur.execute('''
            INSERT OR IGNORE INTO leads (user_id, stage)
            VALUES (?, 'new')
        ''', (user_id,))

        conn.commit()
        conn.close()

    def update_lead_stage(self, user_id, stage):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('UPDATE leads SET stage = ? WHERE user_id = ?', (stage, user_id))
        conn.commit()
        conn.close()

    def get_user(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cur.fetchone()
        conn.close()
        return user

    def update_conversation(self, user_id, message, response):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Получаем текущую историю
        cur.execute('SELECT conversation_history FROM users WHERE user_id = ?', (user_id,))
        result = cur.fetchone()
        history = json.loads(result[0]) if result and result[0] else []

        # Добавляем новое сообщение
        history.append({
            'timestamp': datetime.now().isoformat(),
            'user_message': message,
            'bot_response': response
        })

        # Сохраняем обратно (ограничиваем размер)
        if len(history) > 50:
            history = history[-50:]

        cur.execute('UPDATE users SET conversation_history = ? WHERE user_id = ?',
                   (json.dumps(history), user_id))
        conn.commit()
        conn.close()

    def get_hot_leads(self):
        """Получает горячих лидов для авто-продаж"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            SELECT u.user_id, u.first_name, u.workout_count, l.interest_level
            FROM users u
            JOIN leads l ON u.user_id = l.user_id
            WHERE u.subscription_type = 'trial'
            AND u.workout_count >= 3
            AND l.interest_level >= 3
            AND l.stage = 'engaged'
        ''')
        leads = cur.fetchall()
        conn.close()
        return leads

db = Database()