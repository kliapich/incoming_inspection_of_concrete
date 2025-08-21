#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к Railway PostgreSQL
"""

import os
import sys
from dotenv import load_dotenv
# Загружаем переменные окружения
load_dotenv()

def test_connection():
    """Тестирование подключения к базе данных"""
    print("=== Тестирование подключения к Railway PostgreSQL ===\n")
    
    # Проверяем переменные окружения
    print("📋 Проверка переменных окружения:")
    
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"✅ DATABASE_URL: {database_url[:50]}...")
    else:
        print("❌ DATABASE_URL не найден")
    
    host = os.getenv('RAILWAY_DB_HOST')
    port = os.getenv('RAILWAY_DB_PORT', '5432')
    database = os.getenv('RAILWAY_DB_NAME')
    user = os.getenv('RAILWAY_DB_USER')
    password = os.getenv('RAILWAY_DB_PASSWORD')
    
    if all([host, database, user, password]):
        print(f"✅ RAILWAY_DB_HOST: {host}")
        print(f"✅ RAILWAY_DB_PORT: {port}")
        print(f"✅ RAILWAY_DB_NAME: {database}")
        print(f"✅ RAILWAY_DB_USER: {user}")
        print(f"✅ RAILWAY_DB_PASSWORD: {'*' * len(password)}")
    else:
        print("❌ Не все параметры подключения настроены")
        missing = []
        if not host: missing.append('RAILWAY_DB_HOST')
        if not database: missing.append('RAILWAY_DB_NAME')
        if not user: missing.append('RAILWAY_DB_USER')
        if not password: missing.append('RAILWAY_DB_PASSWORD')
        print(f"   Отсутствуют: {', '.join(missing)}")
    
    print()
    
    # Проверяем тип базы данных
    db_type = os.getenv('DB_TYPE', 'sqlite').lower()
    print(f"🗄️  Тип базы данных: {db_type.upper()}")
    
    # Пробуем импортировать и протестировать подключение
    try:
        print("\n🔌 Тестирование подключения...")
        
        if db_type == 'postgresql':
            import psycopg2
            print("✅ psycopg2 импортирован успешно")
            
            # Пробуем подключиться
            if database_url:
                conn = psycopg2.connect(database_url)
                print("✅ Подключение через DATABASE_URL успешно")
            else:
                conn = psycopg2.connect(
                    host=host,
                    port=int(port),
                    database=database,
                    user=user,
                    password=password
                )
                print("✅ Подключение через параметры успешно")
            
            # Тестируем запрос
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL версия: {version.split(',')[0]}")
            
            cursor.close()
            conn.close()
            print("✅ Соединение закрыто")
            
        else:
            import sqlite3
            print("✅ sqlite3 импортирован успешно")
            
            if os.path.exists('concrete.db'):
                conn = sqlite3.connect('concrete.db')
                print("✅ SQLite подключение успешно")
                
                cursor = conn.cursor()
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]
                print(f"✅ SQLite версия: {version}")
                
                cursor.close()
                conn.close()
                print("✅ Соединение закрыто")
            else:
                print("❌ Файл concrete.db не найден")
        
        print("\n🎉 Тест подключения прошел успешно!")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("   Установите зависимости: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def show_help():
    """Показать справку"""
    print("""
Использование: python test_railway_connection.py [опции]

Опции:
  --help, -h     Показать эту справку
  --env          Показать текущие переменные окружения
  --test         Запустить тест подключения (по умолчанию)

Примеры:
  python test_railway_connection.py
  python test_railway_connection.py --env
  python test_railway_connection.py --help
""")

def show_env():
    """Показать переменные окружения"""
    print("=== Текущие переменные окружения ===\n")
    
    env_vars = [
        'DATABASE_URL',
        'RAILWAY_DB_HOST',
        'RAILWAY_DB_PORT',
        'RAILWAY_DB_NAME',
        'RAILWAY_DB_USER',
        'RAILWAY_DB_PASSWORD',
        'DB_TYPE',
        'USE_SQLITE_FALLBACK',
        'TELEGRAM_BOT_TOKEN'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var or 'TOKEN' in var:
                display_value = '*' * min(len(value), 10)
            else:
                display_value = value
            print(f"{var}: {display_value}")
        else:
            print(f"{var}: не установлен")

def main():
    """Главная функция"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            show_help()
            return
        elif sys.argv[1] == '--env':
            show_env()
            return
        else:
            print(f"Неизвестная опция: {sys.argv[1]}")
            show_help()
            return
    
    # Запускаем тест подключения
    success = test_connection()
    
    if success:
        print("\n💡 Следующие шаги:")
        print("1. Если все работает - можете запускать основное приложение")
        print("2. Если есть ошибки - проверьте настройки в .env файле")
        print("3. Для миграции данных выполните: python migrate_to_railway.py")
    else:
        print("\n🚨 Проблемы с подключением:")
        print("1. Проверьте настройки в .env файле")
        print("2. Убедитесь, что база данных активна в Railway")
        print("3. Проверьте логи выше")

if __name__ == "__main__":
    main()
