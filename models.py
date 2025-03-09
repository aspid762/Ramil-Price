from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    margin = db.Column(db.Float, default=0)
    delivery_fee = db.Column(db.Float, default=0)
    
    # Отношения
    orders = db.relationship('Order', back_populates='customer', lazy='dynamic')
    
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
    customer = db.relationship('Customer', back_populates='orders')
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
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
    quantity = db.Column(db.Float, nullable=False, default=0)
    reserved_quantity = db.Column(db.Float, nullable=False, default=0)
    purchase_price = db.Column(db.Float, nullable=False)
    received_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    @property
    def available_quantity(self):
        """Рассчитывает доступное количество товара"""
        return self.quantity - self.reserved_quantity
    
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