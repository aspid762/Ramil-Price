"""
Скрипт для выполнения миграций базы данных
"""
import os
import sys
import importlib.util

def run_migration(migration_file):
    """Выполняет миграцию из указанного файла"""
    # Получаем абсолютный путь к файлу миграции
    migration_path = os.path.join(os.path.dirname(__file__), 'migrations', migration_file)
    
    # Проверяем, существует ли файл
    if not os.path.exists(migration_path):
        print(f"Файл миграции не найден: {migration_path}")
        return False
    
    # Загружаем модуль миграции
    spec = importlib.util.spec_from_file_location("migration", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    
    # Выполняем основную функцию миграции
    main_function = None
    for attr_name in dir(migration):
        if attr_name.startswith('__'):
            continue
        attr = getattr(migration, attr_name)
        if callable(attr) and attr_name != 'main':
            main_function = attr
            break
    
    if main_function:
        main_function()
        return True
    else:
        print(f"В файле миграции не найдена основная функция: {migration_path}")
        return False

def run_migrations():
    """Выполняет все миграции"""
    # Список файлов миграций в порядке их выполнения
    migrations = [
        'add_weight_per_meter.py',
        'update_stock_weights.py'
    ]
    
    # Выполняем миграции
    for migration in migrations:
        print(f"Выполнение миграции: {migration}")
        if run_migration(migration):
            print(f"Миграция {migration} успешно выполнена")
        else:
            print(f"Ошибка при выполнении миграции {migration}")
            sys.exit(1)
    
    print("Все миграции успешно выполнены")

if __name__ == '__main__':
    run_migrations() 