#!/usr/bin/env python3
"""
Тест для реальных таблиц приложения Beton_control
"""

from database_manager import DatabaseManager

def test_real_tables():
    """Тестирование реальных таблиц приложения"""
    print("=== Тестирование реальных таблиц Beton_control ===\n")
    
    try:
        # Создаем менеджер базы данных
        print("1. Создание менеджера базы данных...")
        db = DatabaseManager('test_beton.db')
        print("✅ Менеджер создан успешно")
        
        # Тестируем вставку организации
        print("\n2. Тестирование вставки организации...")
        org_data = {
            'name': 'ООО "СтройМонтаж"',
            'contact': 'Иванов И.И.',
            'phone': '+7-999-123-45-67'
        }
        
        org_id = db.insert_data('organizations', org_data)
        print(f"✅ Организация вставлена, ID: {org_id}")
        
        # Тестируем вставку объекта
        print("\n3. Тестирование вставки объекта...")
        obj_data = {
            'org_id': org_id,
            'name': 'Жилой дом №1',
            'address': 'ул. Строителей, 15'
        }
        
        obj_id = db.insert_data('objects', obj_data)
        print(f"✅ Объект вставлен, ID: {obj_id}")
        
        # Тестируем вставку конструкции
        print("\n4. Тестирование вставки конструкции...")
        construction_data = {
            'object_id': obj_id,
            'pour_date': '2024-01-15',
            'element': 'Фундамент',
            'concrete_class': 'B25',
            'frost_resistance': 'F150',
            'water_resistance': 'W6',
            'supplier': 'ООО "БетонСтрой"',
            'concrete_passport': 'ПС-001/2024',
            'volume_concrete': 25.5,
            'cubes_count': 3,
            'cones_count': 2,
            'slump': 'С2',
            'temperature': '+18°C',
            'temp_measurements': 5,
            'executor': 'Петров П.П.',
            'act_number': 'АКТ-001/2024',
            'request_number': 'ЗАЯВКА-001/2024'
        }
        
        construction_id = db.insert_data('constructions', construction_data)
        print(f"✅ Конструкция вставлена, ID: {construction_id}")
        
        # Тестируем получение всех данных
        print("\n5. Тестирование получения данных...")
        
        # Организации
        orgs = db.get_all_data('organizations')
        print(f"✅ Организаций: {len(orgs)}")
        for org in orgs:
            print(f"   - ID: {org[0]}, Название: {org[1]}")
        
        # Объекты
        objs = db.get_all_data('objects')
        print(f"✅ Объектов: {len(objs)}")
        for obj in objs:
            print(f"   - ID: {obj[0]}, Название: {obj[2]}, Адрес: {obj[3]}")
        
        # Конструкции
        constructions = db.get_all_data('constructions')
        print(f"✅ Конструкций: {len(constructions)}")
        for const in constructions:
            print(f"   - ID: {const[0]}, Элемент: {const[3]}, Класс: {const[4]}")
        
        # Тестируем получение уникальных значений
        print("\n6. Тестирование получения уникальных значений...")
        concrete_classes = db.fetch_distinct('constructions', 'concrete_class')
        print(f"✅ Уникальные классы бетона: {concrete_classes}")
        
        frost_resistances = db.fetch_distinct('constructions', 'frost_resistance')
        print(f"✅ Уникальные морозостойкости: {frost_resistances}")
        
        # Тестируем обновление данных
        print("\n7. Тестирование обновления данных...")
        update_data = {'volume_concrete': 30.0}
        success = db.update_data('constructions', update_data, 'id = ?', (construction_id,))
        if success:
            print("✅ Объем бетона обновлен успешно")
        
        # Проверяем обновление
        updated_row = db.execute_single('SELECT volume_concrete FROM constructions WHERE id = ?', (construction_id,))
        if updated_row:
            print(f"   - Обновленный объем: {updated_row[0]} м³")
        
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
        if os.path.exists('test_beton.db'):
            os.remove('test_beton.db')
            print("🗑️  Тестовая база данных удалена")

if __name__ == "__main__":
    test_real_tables()
