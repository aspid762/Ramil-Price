from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timedelta

db = SQLAlchemy()

class Product(db.Model):
    """Модель товара в прайс-листе"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    characteristics = db.Column(db.String(200), nullable=False)
    price_per_ton = db.Column(db.Float, nullable=False)
    weight_per_meter = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    @property
    def price_per_meter(self):
        """Рассчитывает цену за погонный метр"""
        return self.price_per_ton * (self.weight_per_meter / 1000)

class PriceHistory(db.Model):
    """Модель истории изменения цен"""
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    price_per_ton = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Отношения
    product = db.relationship('Product', backref=db.backref('price_history', lazy='dynamic'))
    
    def __repr__(self):
        return f'<PriceHistory {self.product_id} {self.created_at}>'

class Customer(db.Model):
    """Модель заказчика"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    margin = db.Column(db.Float, default=0)  # Наценка в процентах
    delivery_fee = db.Column(db.Float, default=0)  # Стоимость доставки
    
    orders = db.relationship('Order', back_populates='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class Order(db.Model):
    """Модель заказа"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False, default='новый')
    expected_shipping = db.Column(db.DateTime, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)  # Добавляем поле для примечаний
    
    # Отношения
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    customer = db.relationship('Customer', back_populates='orders')
    
    @property
    def items_total(self):
        """Рассчитывает общую стоимость позиций заказа без учета доставки"""
        return sum(item.selling_price * item.quantity for item in self.items)

    def __repr__(self):
        return f'<Order {self.id} {self.status}>'

class OrderItem(db.Model):
    """Модель позиции заказа"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    margin = db.Column(db.Float, nullable=False, default=0)
    purchase_price = db.Column(db.Float, nullable=True)  # Для склада
    custom_purchase_price = db.Column(db.Float, nullable=True)  # Ручная цена для закупки
    selling_price = db.Column(db.Float, nullable=False)
    
    # Отношения
    product = db.relationship('Product', backref=db.backref('order_items', lazy='dynamic'))
    stock = db.relationship('Stock', backref=db.backref('order_items', lazy='dynamic'))
    
    def __repr__(self):
        return f'<OrderItem {self.id} for Order {self.order_id}>'

class Stock(db.Model):
    """Модель товара на складе"""
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    characteristics = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0)  # Количество в метрах
    reserved_quantity = db.Column(db.Float, nullable=False, default=0)  # Зарезервированное количество в метрах
    purchase_price = db.Column(db.Float, nullable=False)  # Цена за метр
    weight_per_meter = db.Column(db.Float, nullable=False, default=0)  # Вес 1 метра в кг
    received_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    @property
    def available_quantity(self):
        """Рассчитывает доступное количество товара"""
        return self.quantity - self.reserved_quantity
    
    @property
    def total_weight(self):
        """Рассчитывает общий вес товара в кг"""
        return self.quantity * self.weight_per_meter
    
    @property
    def total_cost(self):
        """Рассчитывает общую стоимость товара"""
        return self.quantity * self.purchase_price
    
    def __repr__(self):
        return f'<Stock {self.category} {self.name}>'

class Shipment(db.Model):
    """Модель отгрузки"""
    __tablename__ = 'shipments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)  # Добавляем внешний ключ
    shipped_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Отношения
    order = db.relationship('Order', backref=db.backref('shipments', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Shipment {self.id} for Order {self.order_id}>'

class StockMovement(db.Model):
    """Модель движения товара на складе"""
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    operation_type = db.Column(db.String(50), nullable=False)  # поступление, резервирование, отгрузка, возврат
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Отношения
    stock = db.relationship('Stock', backref=db.backref('movements', lazy='dynamic'))
    order = db.relationship('Order', backref=db.backref('stock_movements', lazy='dynamic'))
    
    def __repr__(self):
        return f'<StockMovement {self.operation_type} {self.quantity} of {self.stock_id}>'

class Dictionary(db.Model):
    """Модель для хранения справочников"""
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # Тип справочника (категории, статусы и т.д.)
    code = db.Column(db.String(50), nullable=False)  # Код значения (для программного использования)
    name = db.Column(db.String(100), nullable=False)  # Название значения (для отображения)
    sort_order = db.Column(db.Integer, default=0)  # Порядок сортировки
    is_active = db.Column(db.Boolean, default=True)  # Активно ли значение
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('type', 'code', name='uix_dictionary_type_code'),
    )
    
    def __repr__(self):
        return f"<Dictionary {self.type}: {self.code} - {self.name}>" 