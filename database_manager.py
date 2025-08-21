import sqlite3
import os
import logging
from typing import Optional, Union, Dict, Any, List
from contextlib import contextmanager

# Пытаемся загрузить dotenv для Railway
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Переменные окружения загружены")
except ImportError:
    print("⚠️ python-dotenv не установлен, используем системные переменные")

class DatabaseManager:
    """Простой менеджер базы данных SQLite для Beton_control с поддержкой Railway"""
    
    def __init__(self, db_path: str = None):
        # Используем Railway путь или локальный
        self.db_path = db_path or os.getenv('RAILWAY_DB_PATH', 'concrete.db')
        self.connection = None
        self.cursor = None
        self.db_type = 'sqlite'
        self.setup_logging()
        self.init_database()
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Инициализация базы данных: {self.db_path}")
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            # Создаем директорию если нужно
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                self.logger.info(f"Создана директория: {db_dir}")
            
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            self.create_tables()
            self.logger.info(f"База данных SQLite инициализирована: {self.db_path}")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def create_tables(self):
        """Создание таблиц если они не существуют"""
        try:
            # Таблица организаций
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    contact TEXT,
                    phone TEXT
                )
            ''')
            
            # Таблица объектов
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    address TEXT,
                    FOREIGN KEY (org_id) REFERENCES organizations(id)
                )
            ''')
            
            # Таблица конструкций
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS constructions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    pour_date TEXT NOT NULL,
                    element TEXT,
                    concrete_class TEXT,
                    frost_resistance TEXT,
                    water_resistance TEXT,
                    supplier TEXT,
                    concrete_passport TEXT,
                    volume_concrete REAL,
                    cubes_count INTEGER,
                    cones_count INTEGER,
                    slump TEXT,
                    temperature TEXT,
                    temp_measurements INTEGER,
                    executor TEXT,
                    act_number TEXT,
                    request_number TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id)
                )
            ''')
            
            # Миграция: добавляем колонку 'invoice' в constructions, если отсутствует
            self.cursor.execute("PRAGMA table_info(constructions)")
            columns_info = self.cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            if 'invoice' not in column_names:
                self.cursor.execute("ALTER TABLE constructions ADD COLUMN invoice TEXT")
                self.logger.info("Добавлена колонка 'invoice' в таблицу constructions")
            
            self.connection.commit()
            self.logger.info("Таблицы созданы успешно")
        except Exception as e:
            self.logger.error(f"Ошибка создания таблиц: {e}")
            raise
    
    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для работы с курсором"""
        try:
            yield self.cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Ошибка в транзакции: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Выполнение запроса с параметрами"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Ошибка выполнения запроса: {e}")
            raise
    
    def execute_single(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """Выполнение запроса с возвратом одного результата"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Ошибка выполнения запроса: {e}")
            raise
    
    def insert_data(self, table: str, data: Dict[str, Any]) -> int:
        """Вставка данных в таблицу"""
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            with self.get_cursor() as cursor:
                cursor.execute(query, tuple(data.values()))
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Ошибка вставки данных: {e}")
            raise
    
    def update_data(self, table: str, data: Dict[str, Any], condition: str, params: tuple) -> bool:
        """Обновление данных в таблице"""
        try:
            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
            
            with self.get_cursor() as cursor:
                cursor.execute(query, tuple(data.values()) + params)
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Ошибка обновления данных: {e}")
            raise
    
    def delete_data(self, table: str, condition: str, params: tuple) -> bool:
        """Удаление данных из таблицы"""
        try:
            query = f"DELETE FROM {table} WHERE {condition}"
            
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Ошибка удаления данных: {e}")
            raise
    
    def get_all_data(self, table: str, order_by: str = "id") -> List[tuple]:
        """Получение всех данных из таблицы"""
        try:
            query = f"SELECT * FROM {table} ORDER BY {order_by}"
            return self.execute_query(query)
        except Exception as e:
            self.logger.error(f"Ошибка получения данных: {e}")
            raise
    
    def fetch_distinct(self, table: str, column: str) -> List[str]:
        """Получение уникальных значений колонки"""
        try:
            query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}"
            rows = self.execute_query(query)
            return [r[0] for r in rows]
        except Exception as e:
            self.logger.error(f"Ошибка получения уникальных значений: {e}")
            raise
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            self.logger.info("Соединение с базой данных закрыто")
    
    def __enter__(self):
        """Поддержка контекстного менеджера"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие соединения"""
        self.close()