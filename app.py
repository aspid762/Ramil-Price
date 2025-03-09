from flask import Flask, render_template
import datetime
import platform
import os
from config import Config
from models import db, Product, PriceHistory, Customer, Order, OrderItem, Stock, Shipment, StockMovement
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

def create_app(config_class=Config):
    """Создает экземпляр приложения Flask с указанной конфигурацией."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений
    db.init_app(app)
    csrf = CSRFProtect(app)
    migrate = Migrate(app, db)
    
    # Регистрация маршрутов
    from routes.product_routes import product_bp
    from routes.customer_routes import customer_bp
    from routes.order_routes import order_bp
    from routes.stock_routes import stock_bp
    from routes.report_routes import report_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.search_routes import search_bp
    from routes.analytics_routes import analytics_bp
    
    app.register_blueprint(product_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(dashboard_bp, url_prefix='')  # Регистрируем дашборд как корневой маршрут
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(analytics_bp)
    
    @app.route('/health')
    def health():
        """Проверка работоспособности сервиса"""
        return {
            'status': 'ok',
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    @app.route('/info')
    def info():
        """Информация о приложении и окружении"""
        return {
            'app_name': 'Учет продаж металлопроката',
            'version': '1.0.0',
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    return app

# Создаем экземпляр приложения
app = create_app()

# Функция для инициализации базы данных
def init_db():
    """Инициализация базы данных тестовыми данными"""
    # Проверяем, есть ли уже данные в базе
    if Product.query.count() > 0:
        return
    
    # Добавляем товары в прайс-лист
    products = [
        Product(
            category='Арматура',
            name='А500С',
            characteristics='Диаметр 10 мм',
            price_per_ton=65000,
            weight_per_meter=0.617
        ),
        Product(
            category='Арматура',
            name='А500С',
            characteristics='Диаметр 12 мм',
            price_per_ton=65000,
            weight_per_meter=0.888
        ),
        Product(
            category='Труба профильная',
            name='40x20x2',
            characteristics='Прямоугольная',
            price_per_ton=75000,
            weight_per_meter=1.33
        ),
        Product(
            category='Труба профильная',
            name='40x40x2',
            characteristics='Квадратная',
            price_per_ton=75000,
            weight_per_meter=2.47
        ),
        Product(
            category='Профнастил',
            name='С8',
            characteristics='Оцинкованный, толщина 0.5 мм',
            price_per_ton=85000,
            weight_per_meter=4.5
        )
    ]
    
    for product in products:
        db.session.add(product)
    
    # Добавляем заказчиков
    customers = [
        Customer(
            name='ООО "Строитель"',
            phone='+7 (123) 456-78-90',
            address='г. Москва, ул. Строительная, д. 1',
            margin=10.0,
            delivery_fee=2000.0
        ),
        Customer(
            name='ИП Иванов И.И.',
            phone='+7 (987) 654-32-10',
            address='г. Санкт-Петербург, пр. Металлистов, д. 5',
            margin=5.0,
            delivery_fee=1500.0
        )
    ]
    
    for customer in customers:
        db.session.add(customer)
    
    db.session.commit()
    
    # Добавляем товары на склад
    stock_items = [
        Stock(
            category='Арматура',
            name='А500С',
            characteristics='Диаметр 10 мм',
            quantity=1000.0,
            reserved_quantity=0.0,
            purchase_price=60000.0,
            received_at=datetime.datetime.now()
        ),
        Stock(
            category='Труба профильная',
            name='40x20x2',
            characteristics='Прямоугольная',
            quantity=500.0,
            reserved_quantity=0.0,
            purchase_price=70000.0,
            received_at=datetime.datetime.now()
        )
    ]
    
    for item in stock_items:
        db.session.add(item)
    
    db.session.commit()
    
    # Создаем заказы
    order1 = Order(
        customer_id=customers[0].id,
        created_at=datetime.datetime.now(),
        status='новый',
        expected_shipping=datetime.datetime.now() + datetime.timedelta(days=3)
    )
    
    db.session.add(order1)
    db.session.commit()  # Сохраняем заказ, чтобы получить ID
    
    # Добавляем позиции в заказ
    order_item1 = OrderItem(
        order_id=order1.id,
        product_id=products[0].id,
        quantity=100.0,
        margin=customers[0].margin,
        selling_price=products[0].price_per_meter * (1 + customers[0].margin/100)
    )
    
    order_item2 = OrderItem(
        order_id=order1.id,
        product_id=products[2].id,
        quantity=50.0,
        margin=customers[0].margin,
        selling_price=products[2].price_per_meter * (1 + customers[0].margin/100)
    )
    
    db.session.add(order_item1)
    db.session.add(order_item2)
    
    # Создаем второй заказ
    order2 = Order(
        customer_id=customers[1].id,
        created_at=datetime.datetime.now(),
        status='в обработке',
        expected_shipping=datetime.datetime.now() + datetime.timedelta(days=5)
    )
    
    db.session.add(order2)
    db.session.commit()  # Сохраняем заказ, чтобы получить ID
    
    # Добавляем позиции в заказ под закупку
    product = Product.query.filter_by(category='Профнастил').first()
    if product:
        # Ручная закупочная цена
        custom_price = 320  # Цена за метр
        
        order_item3 = OrderItem(
            order_id=order2.id,  # Теперь у нас есть ID заказа
            product_id=product.id,
            quantity=20,
            margin=15.0,
            custom_purchase_price=custom_price,
            selling_price=custom_price * 1.15 * (1 + customers[1].margin/100)
        )
        db.session.add(order_item3)
    
    # Обновляем общую стоимость заказов
    for order in [order1, order2]:
        total = sum(item.selling_price * item.quantity for item in order.items)
        
        # Добавляем стоимость доставки, если есть
        customer = Customer.query.get(order.customer_id)
        if customer and customer.delivery_fee > 0:
            total += customer.delivery_fee
            
        order.total_cost = total
    
    # Добавляем движения товаров на складе
    stock_movement1 = StockMovement(
        stock_id=stock_items[0].id,
        operation_type='поступление',
        quantity=1000.0,
        purchase_price=60000.0,
        created_at=datetime.datetime.now() - datetime.timedelta(days=5)
    )
    
    stock_movement2 = StockMovement(
        stock_id=stock_items[1].id,
        operation_type='поступление',
        quantity=500.0,
        purchase_price=70000.0,
        created_at=datetime.datetime.now() - datetime.timedelta(days=3)
    )
    
    db.session.add(stock_movement1)
    db.session.add(stock_movement2)
    
    db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    with app.app_context():
        init_db()  # Инициализируем БД только при прямом запуске app.py
    app.run(host='0.0.0.0', port=port, debug=True) 