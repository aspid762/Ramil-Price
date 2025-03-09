import os
import re

def fix_datetime_imports(directory='.'):
    """
    Исправляет импорты datetime во всех Python-файлах в указанной директории.
    """
    # Список файлов, которые нужно исключить из обработки
    excluded_files = ['fix_imports.py']
    
    # Список директорий, которые нужно исключить из обработки
    excluded_dirs = ['venv', '.git', '__pycache__', 'migrations']
    
    for root, dirs, files in os.walk(directory):
        # Исключаем директории из обработки
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for file in files:
            # Пропускаем файлы из списка исключений
            if file in excluded_files:
                print(f"Skipping excluded file: {file}")
                continue
                
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Читаем содержимое файла
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    continue
                
                # Флаг для отслеживания изменений
                content_changed = False
                
                # Исправляем неправильные импорты
                if 'from datetime from datetime import' in content:
                    print(f"Fixing imports in {file_path}")
                    
                    # Заменяем неправильные импорты
                    new_content = content.replace('from datetime from datetime import datetime, timedelta, timedelta', 
                                                 'from datetime import datetime, timedelta')
                    
                    if new_content != content:
                        content = new_content
                        content_changed = True
                
                # Исправляем дублирующиеся импорты timedelta
                if 'from datetime import datetime, timedelta, timedelta' in content:
                    print(f"Fixing duplicate imports in {file_path}")
                    
                    # Заменяем дублирующиеся импорты
                    new_content = content.replace('from datetime import datetime, timedelta, timedelta', 
                                                 'from datetime import datetime, timedelta')
                    
                    if new_content != content:
                        content = new_content
                        content_changed = True
                
                # Исправляем старые импорты
                elif 'import datetime' in content:
                    print(f"Fixing old imports in {file_path}")
                    
                    # Заменяем импорты
                    new_content = content.replace('import datetime', 'from datetime import datetime, timedelta')
                    
                    # Заменяем использование
                    new_content = re.sub(r'datetime\.datetime\.', 'datetime.', new_content)
                    new_content = re.sub(r'datetime\.datetime\(', 'datetime(', new_content)
                    new_content = re.sub(r'datetime\.timedelta', 'timedelta', new_content)
                    
                    if new_content != content:
                        content = new_content
                        content_changed = True
                
                # Записываем изменения только если файл был изменен
                if content_changed:
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"Fixed {file_path}")
                    except Exception as e:
                        print(f"Error writing file {file_path}: {e}")

if __name__ == '__main__':
    fix_datetime_imports() 