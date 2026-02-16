import sqlite3
import os
from contextlib import contextmanager
from ..config import config
from ..logger import get_logger

logger = get_logger(__name__)


class Database:
    def __init__(self):
        # Создаем папку для базы данных, если её нет
        db_dir = os.path.dirname(config.DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"✅ Создана папка для БД: {db_dir}")

        self.db_path = config.DATABASE_PATH
        logger.info(f"📁 База данных: {os.path.abspath(self.db_path)}")
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            logger.debug("🔌 Соединение с БД открыто")
            yield conn
        except Exception as e:
            logger.error(f"❌ Ошибка БД: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("🔌 Соединение с БД закрыто")

    def init_db(self):
        try:
            with self.get_connection() as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS agents (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        personality TEXT,
                        mood REAL DEFAULT 0.5,
                        location TEXT DEFAULT 'общая зона',
                        created_at TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        agent_id TEXT,
                        content TEXT,
                        emotion TEXT,
                        timestamp TIMESTAMP,
                        FOREIGN KEY(agent_id) REFERENCES agents(id)
                    );

                    CREATE TABLE IF NOT EXISTS events (
                        id TEXT PRIMARY KEY,
                        content TEXT,
                        agent_id TEXT,
                        type TEXT,
                        timestamp TIMESTAMP
                    );
                """)
                conn.commit()
                logger.info("✅ Таблицы созданы или уже существуют")
        except Exception as e:
            logger.error(f"❌ Ошибка при создании таблиц: {e}")

    def execute(self, query: str, params: tuple = ()):
        logger.debug(f"⚡ SQL Execute: {query[:50]}...")
        with self.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()

    def fetch_one(self, query: str, params: tuple = ()):
        logger.debug(f"🔍 SQL FetchOne: {query[:50]}...")
        with self.get_connection() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()):
        logger.debug(f"📋 SQL FetchAll: {query[:50]}...")
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]


db = Database()