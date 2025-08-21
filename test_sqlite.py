#!/usr/bin/env python3
"""
Простой тест для SQLite базы данных
"""

from database_manager import DatabaseManager

def test_sqlite():
    """Тестирование SQLite базы данных"""
    print("=== Тестирование SQLite базы данных ===\n")
    
    try:
        # Создаем менеджер базы данных
        print("1. Создание менеджера базы данных...")
        db = DatabaseManager('test_concrete.db')
        print("✅ Менеджер создан успешно")
        
        # Тестируем вставку данных
        print("\n2. Тестирование вставки данных...")
        test_data = {
            'date': '2024-01-15',
            'concrete_type': 'B25',
            'strength': 28.5,
            'notes': 'Тестовый образец'
        }
        
        concrete_id = db.insert_data('concrete_data', test_data)
        print(f"✅ Данные вставлены, ID: {concrete_id}")
        
        # Тестируем получение данных
        print("\n3. Тестирование получения данных...")
        all_data = db.get_all_data('concrete_data')
        print(f"✅ Получено записей: {len(all_data)}")
        
        for row in all_data:
            print(f"   - ID: {row[0]}, Тип: {row[2]}, Прочность: {row[3]}")
        
        # Тестируем обновление данных
        print("\n4. Тестирование обновления данных...")
        update_data = {'strength': 30.0}
        success = db.update_data('concrete_data', update_data, 'id = ?', (concrete_id,))
        if success:
            print("✅ Данные обновлены успешно")
        
        # Проверяем обновление
        updated_row = db.execute_single('SELECT * FROM concrete_data WHERE id = ?', (concrete_id,))
        if updated_row:
            print(f"   - Обновленная прочность: {updated_row[3]}")
        
        # Тестируем удаление данных
        print("\n5. Тестирование удаления данных...")
        success = db.delete_data('concrete_data', 'id = ?', (concrete_id,))
        if success:
            print("✅ Данные удалены успешно")
        
        # Проверяем удаление
        remaining_data = db.get_all_data('concrete_data')
        print(f"   - Осталось записей: {len(remaining_data)}")
        
        print("\n🎉 Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Закрываем соединение
        if 'db' in locals():
            db.close()
            print("\n🔒 Соединение с базой данных закрыто")
        
        # Удаляем тестовую базу
        import os
        if os.path.exists('test_concrete.db'):
            os.remove('test_concrete.db')
            print("🗑️  Тестовая база данных удалена")

if __name__ == "__main__":
    test_sqlite()
