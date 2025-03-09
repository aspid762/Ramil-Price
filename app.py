from flask import Flask, render_template
from datetime import datetime, timedelta, timedelta, timedelta, timedelta
import platform
import os
from config import Config
from models import db, Product, PriceHistory, Customer, Order, OrderItem, Stock, StockMovement
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from urllib.parse import quote

def create_app(config_class=Config):
    """Создает экземпляр приложения Flask с указанной конфигурацией."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Добавляем фильтр urlencode для шаблонов
    app.jinja_env.filters['urlencode'] = lambda u: quote(u)
    
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
    def health_check():
        """Проверка работоспособности приложения."""
        return {
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'python_version': platform.python_version(),
            'platform': platform.platform()
        }
    
    # Проверяем существование базы данных и создаем её при необходимости
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        db_exists = os.path.exists(db_path)
        
        # Создаем таблицы, если они не существуют
        db.create_all()
        
        # Проверяем, есть ли данные в таблицах
        if not db_exists or Product.query.count() == 0:
            print("База данных пуста. Заполняем тестовыми данными...")
            init_db()  # Заполняем тестовыми данными только если БД пуста
        else:
            print(f"База данных уже содержит данные. Пропускаем инициализацию.")
    
    return app

def init_db():
    """Инициализирует базу данных тестовыми данными."""
    print("Заполнение базы данных тестовыми данными...")
    
    # Проверяем, есть ли уже данные в таблицах
    if Product.query.count() > 0 or Customer.query.count() > 0:
        print("В базе данных уже есть записи. Пропускаем инициализацию.")
        return
    
    # Создаем тестовых заказчиков
    customer1 = Customer(
        name='ООО "Стройкомплект"',
        phone='+7 (123) 456-78-90',
        address='г. Москва, ул. Строителей, 10',
        margin=5.0,
        delivery_fee=2000.0
    )
    
    customer2 = Customer(
        name='ИП Иванов А.А.',
        phone='+7 (987) 654-32-10',
        address='г. Санкт-Петербург, пр. Ленина, 25',
        margin=3.0,
        delivery_fee=1500.0
    )
    
    db.session.add(customer1)
    db.session.add(customer2)
    db.session.commit()
    
    # Создаем тестовые товары
    product1 = Product(
        category='Трубы',
        name='Труба профильная',
        characteristics='40x20x2 мм',
        price_per_ton=65000.0,
        weight_per_meter=1.78
    )
    
    product2 = Product(
        category='Трубы',
        name='Труба круглая',
        characteristics='Ø32x3 мм',
        price_per_ton=70000.0,
        weight_per_meter=2.12
    )
    
    product3 = Product(
        category='Листы',
        name='Лист горячекатаный',
        characteristics='3 мм',
        price_per_ton=60000.0,
        weight_per_meter=23.55
    )
    
    db.session.add(product1)
    db.session.add(product2)
    db.session.add(product3)
    db.session.commit()
    
    # Создаем тестовые позиции на складе
    stock_items = [
        Stock(
            category='Трубы',
            name='Труба профильная',
            characteristics='40x20x2 мм',
            quantity=1000.0,
            reserved_quantity=0.0,
            purchase_price=60000.0,
            received_at=datetime.now() - timedelta(days=10)
        ),
        Stock(
            category='Трубы',
            name='Труба круглая',
            characteristics='Ø32x3 мм',
            quantity=500.0,
            reserved_quantity=0.0,
            purchase_price=65000.0,
            received_at=datetime.now() - timedelta(days=7)
        ),
        Stock(
            category='Листы',
            name='Лист горячекатаный',
            characteristics='3 мм',
            quantity=300.0,
            reserved_quantity=0.0,
            purchase_price=55000.0,
            received_at=datetime.now() - timedelta(days=5)
        )
    ]
    
    for item in stock_items:
        db.session.add(item)
    
    db.session.commit()
    
    # Создаем тестовые движения товаров
    stock_movement1 = StockMovement(
        stock_id=stock_items[0].id,
        operation_type='поступление',
        quantity=1000.0,
        purchase_price=60000.0,
        created_at=datetime.now() - timedelta(days=5)
    )
    
    stock_movement2 = StockMovement(
        stock_id=stock_items[1].id,
        operation_type='поступление',
        quantity=500.0,
        purchase_price=70000.0,
        created_at=datetime.now() - timedelta(days=3)
    )
    
    db.session.add(stock_movement1)
    db.session.add(stock_movement2)
    
    db.session.commit()
    
    # Создаем тестовые заказы
    order1 = Order(
        customer_id=customer1.id,
        status='новый',
        created_at=datetime.now() - timedelta(days=2),
        expected_shipping=datetime.now() + timedelta(days=3)
    )
    
    order2 = Order(
        customer_id=customer2.id,
        status='в обработке',
        created_at=datetime.now() - timedelta(days=1),
        expected_shipping=datetime.now() + timedelta(days=2)
    )
    
    db.session.add(order1)
    db.session.add(order2)
    db.session.commit()
    
    # Создаем тестовые позиции заказов
    order_item1 = OrderItem(
        order_id=order1.id,
        product_id=product1.id,
        quantity=100.0,
        selling_price=product1.price_per_meter
    )
    
    order_item2 = OrderItem(
        order_id=order1.id,
        product_id=product2.id,
        quantity=50.0,
        selling_price=product2.price_per_meter
    )
    
    order_item3 = OrderItem(
        order_id=order2.id,
        product_id=product3.id,
        quantity=20.0,
        selling_price=product3.price_per_meter
    )
    
    db.session.add(order_item1)
    db.session.add(order_item2)
    db.session.add(order_item3)
    
    # Обновляем общую стоимость заказов
    order1.total_cost = sum(item.selling_price * item.quantity for item in [order_item1, order_item2])
    order2.total_cost = sum(item.selling_price * item.quantity for item in [order_item3])
    
    db.session.commit()
    
    print("База данных успешно заполнена тестовыми данными.")

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 