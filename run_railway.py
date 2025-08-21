#!/usr/bin/env python3
"""
Скрипт для запуска приложения Beton_control с поддержкой Railway PostgreSQL
"""

import os
import sys
from dotenv import load_dotenv

def main():
    """Главная функция запуска"""
    print("🚀 Запуск Beton_control с поддержкой Railway PostgreSQL")
    print("=" * 60)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("⚠️  Файл .env не найден!")
        print("📋 Создайте файл .env на основе config.env.example")
        print("🔧 Настройте параметры подключения к Railway")
        return
    
    # Проверяем основные переменные
    db_type = os.getenv('DB_TYPE', 'sqlite').lower()
    print(f"🗄️  Тип базы данных: {db_type.upper()}")
    
    if db_type == 'postgresql':
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            print("✅ DATABASE_URL настроен")
        else:
            host = os.getenv('RAILWAY_DB_HOST')
            if host:
                print(f"✅ Подключение к Railway: {host}")
            else:
                print("❌ Параметры Railway не настроены")
                return
    else:
        print("ℹ️  Используется SQLite")
    
    print()
    print("🔌 Тестирование подключения...")
    
    try:
        # Импортируем и тестируем подключение
        from database_manager import DatabaseManager
        db = DatabaseManager()
        
        db_info = db.get_connection_info()
        print(f"✅ Подключение: {db_info['type']}")
        print(f"📊 Статус: {db_info['status']}")
        
        if db.test_connection():
            print("✅ Тест соединения прошел успешно")
        else:
            print("❌ Тест соединения не прошел")
            return
        
        db.close()
        
    except ImportError:
        print("❌ Не удалось импортировать менеджер базы данных")
        print("📦 Установите зависимости: pip install -r requirements.txt")
        return
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return
    
    print()
    print("🎯 Запуск приложения...")
    
    try:
        # Запускаем основное приложение
        from Beton_control_railway import main as app_main
        app_main()
    except ImportError:
        print("❌ Не удалось импортировать основное приложение")
        print("📁 Убедитесь, что файл Beton_control_railway.py существует")
        return
    except Exception as e:
        print(f"❌ Ошибка запуска приложения: {e}")
        return

if __name__ == "__main__":
    main()
