import os

# Пытаемся импортировать dotenv, но не вызываем ошибку, если модуль не установлен
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Если модуль не установлен, просто продолжаем без него
    pass

class Config:
    # Базовая конфигурация
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///metal_sales.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Предопределенные группы товаров
    PRODUCT_CATEGORIES = [
        'Проф. труба', 
        'Уголок', 
        'Труба круг.', 
        'Профнастил', 
        'Арматура Рифленая'
    ]
    
    # Статусы заказов
    ORDER_STATUSES = [
        'новый', 
        'в обработке',
        'передан заказчику на согласование',
        'принят заказчиком',
        'оплачен полностью',
        'оплачен частично',
        'отгружен'
    ]
    
    # Типы операций на складе
    STOCK_OPERATION_TYPES = [
        'поступление', 
        'резервирование', 
        'отгрузка'
    ] 