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
    
    # Функции для получения справочников из базы данных
    @staticmethod
    def get_product_categories():
        """Получает список категорий товаров из базы данных"""
        from models import Dictionary
        from flask import current_app
        
        with current_app.app_context():
            categories = Dictionary.query.filter_by(type='product_categories', is_active=True).order_by(Dictionary.sort_order, Dictionary.name).all()
            return [category.name for category in categories] or ['Трубы', 'Листы', 'Арматура', 'Прочее']
    
    @staticmethod
    def get_order_statuses():
        """Получает список статусов заказов из базы данных"""
        from models import Dictionary
        from flask import current_app
        
        with current_app.app_context():
            statuses = Dictionary.query.filter_by(type='order_statuses', is_active=True).order_by(Dictionary.sort_order, Dictionary.name).all()
            return [status.name for status in statuses] or ['новый', 'в обработке', 'подтвержден', 'отгружен', 'отменен']
    
    @staticmethod
    def get_stock_operation_types():
        """Получает список типов операций со складом из базы данных"""
        from models import Dictionary
        from flask import current_app
        
        with current_app.app_context():
            types = Dictionary.query.filter_by(type='stock_operation_types', is_active=True).order_by(Dictionary.sort_order, Dictionary.name).all()
            return [type.name for type in types] or ['поступление', 'отгрузка', 'списание', 'инвентаризация', 'резервирование', 'отмена резервирования']
    
    # Свойства для доступа к справочникам
    @property
    def PRODUCT_CATEGORIES(self):
        return self.get_product_categories()
    
    @property
    def ORDER_STATUSES(self):
        return self.get_order_statuses()
    
    @property
    def STOCK_OPERATION_TYPES(self):
        return self.get_stock_operation_types()

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