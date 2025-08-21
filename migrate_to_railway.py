#!/usr/bin/env python3
"""
Скрипт миграции данных из SQLite в PostgreSQL Railway
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any
import sys

# Загружаем переменные окружения
load_dotenv()

class DataMigrator:
    """Класс для миграции данных из SQLite в PostgreSQL"""
    
    def __init__(self):
        self.setup_logging()
        self.sqlite_conn = None
        self.postgres_conn = None
        
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_sqlite(self):
        """Подключение к SQLite базе данных"""
        try:
            if not os.path.exists('concrete.db'):
                self.logger.error("Файл concrete.db не найден")
                return False
            
            self.sqlite_conn = sqlite3.connect('concrete.db')
            self.logger.info("Подключение к SQLite успешно")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка подключения к SQLite: {e}")
            return False
    
    def connect_postgresql(self):
        """Подключение к PostgreSQL Railway"""
        try:
            # Пробуем подключиться через DATABASE_URL
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                self.postgres_conn = psycopg2.connect(database_url)
                self.logger.info("Подключение к PostgreSQL через DATABASE_URL успешно")
            else:
                # Пробуем подключиться через отдельные параметры
                self.postgres_conn = psycopg2.connect(
                    host=os.getenv('RAILWAY_DB_HOST'),
                    port=os.getenv('RAILWAY_DB_PORT', 5432),
                    database=os.getenv('RAILWAY_DB_NAME'),
                    user=os.getenv('RAILWAY_DB_USER'),
                    password=os.getenv('RAILWAY_DB_PASSWORD')
                )
                self.logger.info("Подключение к PostgreSQL через параметры успешно")
            
            return True
        except Exception as e:
            self.logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            return False
    
    def create_tables_postgresql(self):
        """Создание таблиц в PostgreSQL"""
        scripts = [
            """CREATE TABLE IF NOT EXISTS organizations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                contact VARCHAR(255),
                phone VARCHAR(50)
            )""",
            """CREATE TABLE IF NOT EXISTS objects (
                id SERIAL PRIMARY KEY,
                org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                address TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS constructions (
                id SERIAL PRIMARY KEY,
                object_id INTEGER NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
                pour_date VARCHAR(20),
                element TEXT,
                concrete_class VARCHAR(50),
                frost_resistance VARCHAR(20),
                water_resistance VARCHAR(20),
                supplier VARCHAR(255),
                concrete_passport VARCHAR(255),
                volume_concrete DECIMAL(10,2),
                cubes_count INTEGER,
                cones_count INTEGER,
                slump VARCHAR(50),
                temperature VARCHAR(50),
                temp_measurements INTEGER,
                executor VARCHAR(255),
                act_number VARCHAR(100),
                request_number VARCHAR(100),
                invoice VARCHAR(100)
            )"""
        ]
        
        cursor = self.postgres_conn.cursor()
        for script in scripts:
            try:
                cursor.execute(script)
                self.logger.info("Таблица создана успешно")
            except Exception as e:
                self.logger.warning(f"Таблица уже существует или ошибка: {e}")
        
        # Проверяем наличие колонки invoice
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'constructions' AND column_name = 'invoice'
            """)
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE constructions ADD COLUMN invoice VARCHAR(100)")
                self.logger.info("Колонка 'invoice' добавлена")
        except Exception as e:
            self.logger.warning(f"Ошибка при проверке колонки 'invoice': {e}")
        
        self.postgres_conn.commit()
        cursor.close()
    
    def migrate_organizations(self) -> Dict[int, int]:
        """Миграция организаций"""
        self.logger.info("Начинаем миграцию организаций...")
        
        cursor_sqlite = self.sqlite_conn.cursor()
        cursor_postgres = self.postgres_conn.cursor()
        
        # Получаем данные из SQLite
        cursor_sqlite.execute("SELECT id, name, contact, phone FROM organizations")
        organizations = cursor_sqlite.fetchall()
        
        id_mapping = {}  # Старый ID -> Новый ID
        
        for old_id, name, contact, phone in organizations:
            try:
                cursor_postgres.execute(
                    "INSERT INTO organizations (name, contact, phone) VALUES (%s, %s, %s) RETURNING id",
                    (name, contact, phone)
                )
                new_id = cursor_postgres.fetchone()[0]
                id_mapping[old_id] = new_id
                self.logger.info(f"Организация '{name}' мигрирована (ID: {old_id} -> {new_id})")
            except Exception as e:
                self.logger.error(f"Ошибка миграции организации '{name}': {e}")
        
        self.postgres_conn.commit()
        cursor_sqlite.close()
        cursor_postgres.close()
        
        self.logger.info(f"Мигрировано организаций: {len(id_mapping)}")
        return id_mapping
    
    def migrate_objects(self, org_id_mapping: Dict[int, int]) -> Dict[int, int]:
        """Миграция объектов"""
        self.logger.info("Начинаем миграцию объектов...")
        
        cursor_sqlite = self.sqlite_conn.cursor()
        cursor_postgres = self.postgres_conn.cursor()
        
        # Получаем данные из SQLite
        cursor_sqlite.execute("SELECT id, org_id, name, address FROM objects")
        objects = cursor_sqlite.fetchall()
        
        id_mapping = {}  # Старый ID -> Новый ID
        
        for old_id, old_org_id, name, address in objects:
            if old_org_id in org_id_mapping:
                new_org_id = org_id_mapping[old_org_id]
                try:
                    cursor_postgres.execute(
                        "INSERT INTO objects (org_id, name, address) VALUES (%s, %s, %s) RETURNING id",
                        (new_org_id, name, address)
                    )
                    new_id = cursor_postgres.fetchone()[0]
                    id_mapping[old_id] = new_id
                    self.logger.info(f"Объект '{name}' мигрирован (ID: {old_id} -> {new_id})")
                except Exception as e:
                    self.logger.error(f"Ошибка миграции объекта '{name}': {e}")
            else:
                self.logger.warning(f"Пропускаем объект '{name}' - организация не найдена")
        
        self.postgres_conn.commit()
        cursor_sqlite.close()
        cursor_postgres.close()
        
        self.logger.info(f"Мигрировано объектов: {len(id_mapping)}")
        return id_mapping
    
    def migrate_constructions(self, obj_id_mapping: Dict[int, int]):
        """Миграция конструктивов"""
        self.logger.info("Начинаем миграцию конструктивов...")
        
        cursor_sqlite = self.sqlite_conn.cursor()
        cursor_postgres = self.postgres_conn.cursor()
        
        # Получаем данные из SQLite
        cursor_sqlite.execute("""
            SELECT object_id, pour_date, element, concrete_class, frost_resistance, 
                   water_resistance, supplier, concrete_passport, volume_concrete, 
                   cubes_count, cones_count, slump, temperature, temp_measurements, 
                   executor, act_number, request_number, invoice
            FROM constructions
        """)
        constructions = cursor_sqlite.fetchall()
        
        migrated_count = 0
        
        for (old_obj_id, pour_date, element, concrete_class, frost_resistance,
             water_resistance, supplier, concrete_passport, volume_concrete,
             cubes_count, cones_count, slump, temperature, temp_measurements,
             executor, act_number, request_number, invoice) in constructions:
            
            if old_obj_id in obj_id_mapping:
                new_obj_id = obj_id_mapping[old_obj_id]
                try:
                    cursor_postgres.execute("""
                        INSERT INTO constructions (
                            object_id, pour_date, element, concrete_class, frost_resistance,
                            water_resistance, supplier, concrete_passport, volume_concrete,
                            cubes_count, cones_count, slump, temperature, temp_measurements,
                            executor, act_number, request_number, invoice
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        new_obj_id, pour_date, element, concrete_class, frost_resistance,
                        water_resistance, supplier, concrete_passport, volume_concrete,
                        cubes_count, cones_count, slump, temperature, temp_measurements,
                        executor, act_number, request_number, invoice
                    ))
                    migrated_count += 1
                except Exception as e:
                    self.logger.error(f"Ошибка миграции конструкции: {e}")
            else:
                self.logger.warning(f"Пропускаем конструктив - объект не найден")
        
        self.postgres_conn.commit()
        cursor_sqlite.close()
        cursor_postgres.close()
        
        self.logger.info(f"Мигрировано конструктивов: {migrated_count}")
    
    def verify_migration(self):
        """Проверка результатов миграции"""
        self.logger.info("Проверяем результаты миграции...")
        
        cursor_sqlite = self.sqlite_conn.cursor()
        cursor_postgres = self.postgres_conn.cursor()
        
        # Проверяем количество записей
        tables = ['organizations', 'objects', 'constructions']
        
        for table in tables:
            cursor_sqlite.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = cursor_sqlite.fetchone()[0]
            
            cursor_postgres.execute(f"SELECT COUNT(*) FROM {table}")
            postgres_count = cursor_postgres.fetchone()[0]
            
            self.logger.info(f"{table}: SQLite - {sqlite_count}, PostgreSQL - {postgres_count}")
        
        cursor_sqlite.close()
        cursor_postgres.close()
    
    def run_migration(self):
        """Запуск полной миграции"""
        try:
            # Подключаемся к базам данных
            if not self.connect_sqlite():
                return False
            
            if not self.connect_postgresql():
                return False
            
            # Создаем таблицы в PostgreSQL
            self.create_tables_postgresql()
            
            # Мигрируем данные
            org_id_mapping = self.migrate_organizations()
            obj_id_mapping = self.migrate_objects(org_id_mapping)
            self.migrate_constructions(obj_id_mapping)
            
            # Проверяем результаты
            self.verify_migration()
            
            self.logger.info("Миграция завершена успешно!")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка миграции: {e}")
            return False
        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()
            if self.postgres_conn:
                self.postgres_conn.close()
    
    def close_connections(self):
        """Закрытие всех соединений"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.postgres_conn:
            self.postgres_conn.close()

def main():
    """Главная функция"""
    print("=== Миграция данных из SQLite в PostgreSQL Railway ===")
    print()
    
    # Проверяем наличие переменных окружения
    required_vars = ['DATABASE_URL'] or ['RAILWAY_DB_HOST', 'RAILWAY_DB_NAME', 'RAILWAY_DB_USER', 'RAILWAY_DB_PASSWORD']
    
    if not any(os.getenv(var) for var in ['DATABASE_URL', 'RAILWAY_DB_HOST']):
        print("ОШИБКА: Не настроены переменные окружения для PostgreSQL")
        print("Создайте файл .env на основе config.env.example")
        return
    
    # Запускаем миграцию
    migrator = DataMigrator()
    
    try:
        success = migrator.run_migration()
        if success:
            print("\n✅ Миграция завершена успешно!")
            print("Теперь можете использовать PostgreSQL Railway")
        else:
            print("\n❌ Миграция завершилась с ошибками")
            print("Проверьте логи выше")
    except KeyboardInterrupt:
        print("\n⚠️ Миграция прервана пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
    finally:
        migrator.close_connections()

if __name__ == "__main__":
    main()
