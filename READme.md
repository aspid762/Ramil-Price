# Тестовое приложение на Flask

Простое приложение на Python Flask для проверки работоспособности сервиса.

## Установка

1. Клонировать репозиторий
2. Создать виртуальное окружение (один из способов):
   ```
   # Способ 1: стандартный venv
   python -m venv venv
   
   # Способ 2: использование virtualenv
   pip install virtualenv
   virtualenv venv
   
   # Способ 3: использование --system-site-packages
   # Этот способ позволит использовать глобально установленные пакеты
   python -m venv venv --system-site-packages
   ```
3. Активировать виртуальное окружение:
   ```
   source venv/bin/activate  # Для Linux/Mac
   venv\Scripts\activate     # Для Windows
   ```
4. Установить зависимости: 
   ```
   # ВАЖНО: не забудьте флаг -r
   pip install -r requirements.txt
   
   # Если возникают проблемы с SSL, используйте:
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```
5. Запустить приложение: `python app.py`

## Эндпоинты

- `/` - Главная страница с приветствием
- `/health` - Эндпоинт для проверки работоспособности
- `/info` - Информация о приложении

## Тестирование

Для запуска тестов выполните: `python test_app.py`

## Решение проблем

### Распространенные ошибки

1. **Ошибка при установке пакетов**: Убедитесь, что используете команду `pip install -r requirements.txt` (с флагом `-r`), а не `pip install requirements.txt`.

2. **Проблемы с SSL**: Если возникают ошибки SSL при установке пакетов, попробуйте:
   ```
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

3. **Проблемы с созданием виртуального окружения**: Если не удается создать виртуальное окружение, можно установить пакеты глобально:
   ```
   pip install -r requirements.txt
   ```
