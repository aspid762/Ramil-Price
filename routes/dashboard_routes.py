from flask import Blueprint, render_template
from models import db, Product, Customer, Order, Stock, StockMovement
from sqlalchemy import func
import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Главная страница с дашбордом"""
    # Получаем статистику
    stats = {
        'products_count': Product.query.count(),
        'customers_count': Customer.query.count(),
        'orders_count': Order.query.count(),
        'stock_items_count': Stock.query.count(),
        'total_stock_value': db.session.query(func.sum(Stock.quantity * Stock.purchase_price)).scalar() or 0,
    }
    
    # Получаем последние заказы
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Убедимся, что у всех заказов есть total_cost
    for order in recent_orders:
        if order.total_cost is None:
            # Рассчитываем стоимость позиций
            items_total = sum(item.selling_price * item.quantity for item in order.items) if order.items else 0
            
            # Добавляем стоимость доставки, если есть
            if order.customer and order.customer.delivery_fee:
                items_total += order.customer.delivery_fee
            
            order.total_cost = items_total
    
    # Получаем товары с низким запасом
    low_stock_items = Stock.query.filter(Stock.quantity - Stock.reserved_quantity < 10).limit(5).all()
    
    # Получаем данные для графика продаж по месяцам
    current_year = datetime.datetime.now().year
    sales_by_month = []
    
    for month in range(1, 13):
        start_date = datetime.datetime(current_year, month, 1)
        if month == 12:
            end_date = datetime.datetime(current_year + 1, 1, 1)
        else:
            end_date = datetime.datetime(current_year, month + 1, 1)
        
        # Сумма продаж за месяц
        monthly_sales = db.session.query(func.sum(Order.total_cost))\
            .filter(Order.created_at >= start_date, Order.created_at < end_date)\
            .scalar() or 0
        
        sales_by_month.append({
            'month': start_date.strftime('%B'),
            'sales': float(monthly_sales)
        })
    
    # Получаем данные для графика движения товаров
    stock_movements = db.session.query(
        func.date(StockMovement.created_at).label('date'),
        func.sum(StockMovement.quantity).label('quantity')
    ).group_by(func.date(StockMovement.created_at))\
     .order_by(func.date(StockMovement.created_at).desc())\
     .limit(30).all()
    
    stock_movement_data = [
        {
            'date': movement.date.strftime('%Y-%m-%d') if hasattr(movement.date, 'strftime') else movement.date,
            'quantity': float(movement.quantity)
        } for movement in stock_movements
    ]
    
    return render_template(
        'dashboard/index.html',
        stats=stats,
        recent_orders=recent_orders,
        low_stock_items=low_stock_items,
        sales_by_month=sales_by_month,
        stock_movement_data=stock_movement_data
    ) 