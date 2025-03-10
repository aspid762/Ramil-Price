from flask import Blueprint, render_template, request
from models import db, Order, OrderItem, Product, Customer
from sqlalchemy import func, extract, desc
from datetime import datetime, timedelta, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
def index():
    """Главная страница аналитики"""
    return render_template('analytics/index.html')

@analytics_bp.route('/sales')
def sales():
    """Аналитика продаж"""
    # Получаем период для анализа
    period = request.args.get('period', 'month')
    
    # Определяем начальную дату в зависимости от периода
    today = datetime.now()
    if period == 'week':
        start_date = today - timedelta(days=7)
        group_by = func.date(Order.created_at)
        date_format = '%d.%m.%Y'
    elif period == 'month':
        start_date = today - timedelta(days=30)
        group_by = func.date(Order.created_at)
        date_format = '%d.%m.%Y'
    elif period == 'quarter':
        start_date = today - timedelta(days=90)
        group_by = func.date_trunc('week', Order.created_at)
        date_format = '%d.%m.%Y'
    elif period == 'year':
        start_date = today - timedelta(days=365)
        group_by = func.date_trunc('month', Order.created_at)
        date_format = '%m.%Y'
    else:
        start_date = today - timedelta(days=30)
        group_by = func.date(Order.created_at)
        date_format = '%d.%m.%Y'
    
    # Получаем данные о продажах по дням/неделям/месяцам
    sales_by_date = db.session.query(
        group_by.label('date'),
        func.sum(Order.total_cost).label('total')
    ).filter(
        Order.created_at >= start_date,
        Order.status != 'отменен'
    ).group_by(
        group_by
    ).order_by(
        group_by
    ).all()
    
    # Преобразуем данные для графика
    sales_data = []
    for date_item in sales_by_date:
        date_str = ""
        if hasattr(date_item.date, 'strftime'):
            date_str = date_item.date.strftime(date_format)
        elif hasattr(date_item.date, 'isoformat'):
            date_str = date_item.date.isoformat()
        else:
            date_str = str(date_item.date)
        
        sales_data.append({
            'date': date_str,
            'total': float(date_item.total)
        })
    
    # Получаем топ-5 самых продаваемых товаров
    top_products = db.session.query(
        Product.category,
        Product.name,
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.created_at >= start_date,
        Order.status != 'отменен'
    ).group_by(
        Product.id
    ).order_by(
        desc('total_quantity')
    ).limit(5).all()
    
    # Получаем топ-5 заказчиков по сумме заказов
    top_customers = db.session.query(
        Customer.name,
        func.sum(Order.total_cost).label('total_amount')
    ).join(
        Order, Customer.id == Order.customer_id
    ).filter(
        Order.created_at >= start_date,
        Order.status != 'отменен'
    ).group_by(
        Customer.id
    ).order_by(
        desc('total_amount')
    ).limit(5).all()
    
    # Получаем общую статистику
    stats = {
        'total_sales': db.session.query(func.sum(Order.total_cost)).filter(
            Order.created_at >= start_date,
            Order.status != 'отменен'
        ).scalar() or 0,
        'orders_count': db.session.query(func.count(Order.id)).filter(
            Order.created_at >= start_date,
            Order.status != 'отменен'
        ).scalar() or 0,
        'average_order': db.session.query(func.avg(Order.total_cost)).filter(
            Order.created_at >= start_date,
            Order.status != 'отменен'
        ).scalar() or 0
    }
    
    return render_template(
        'analytics/sales.html',
        period=period,
        sales_data=sales_data,
        top_products=top_products,
        top_customers=top_customers,
        stats=stats
    )

@analytics_bp.route('/products')
def products():
    """Аналитика по товарам"""
    # Получаем период для анализа
    period = request.args.get('period', 'month')
    
    # Определяем начальную дату в зависимости от периода
    today = datetime.now()
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'quarter':
        start_date = today - timedelta(days=90)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)
    
    # Получаем данные о продажах по категориям товаров
    sales_by_category = db.session.query(
        Product.category,
        func.sum(OrderItem.quantity * OrderItem.selling_price).label('total_sales')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.created_at >= start_date,
        Order.status != 'отменен'
    ).group_by(
        Product.category
    ).order_by(
        desc('total_sales')
    ).all()
    
    # Преобразуем данные для графика
    category_data = [
        {
            'category': category.category,
            'total': float(category.total_sales)
        }
        for category in sales_by_category
    ]
    
    # Получаем данные о количестве проданных товаров по категориям
    quantity_by_category = db.session.query(
        Product.category,
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.created_at >= start_date,
        Order.status != 'отменен'
    ).group_by(
        Product.category
    ).order_by(
        desc('total_quantity')
    ).all()
    
    # Преобразуем данные для графика
    quantity_data = [
        {
            'category': category.category,
            'quantity': float(category.total_quantity)
        }
        for category in quantity_by_category
    ]
    
    # Получаем топ-10 самых продаваемых товаров
    top_products = db.session.query(
        Product.category,
        Product.name,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.quantity * OrderItem.selling_price).label('total_sales')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.created_at >= start_date,
        Order.status != 'отменен'
    ).group_by(
        Product.id
    ).order_by(
        desc('total_quantity')
    ).limit(10).all()
    
    return render_template(
        'analytics/products.html',
        period=period,
        category_data=category_data,
        quantity_data=quantity_data,
        top_products=top_products
    )

@analytics_bp.route('/customers')
def customers():
    """Аналитика по заказчикам"""
    period = request.args.get('period', 'month')
    
    # Получаем топ заказчиков по сумме заказов
    top_customers = db.session.query(
        Customer,
        func.sum(Order.total_cost).label('total_spent'),
        func.count(Order.id).label('orders_count'),
        func.avg(Order.total_cost).label('average_order')
    ).join(Order).group_by(Customer.id).order_by(
        desc('total_spent')
    ).limit(10).all()
    
    # Подзапрос для получения даты первого заказа каждого заказчика
    first_orders = db.session.query(
        Order.customer_id,
        func.min(Order.created_at).label('first_order_date')
    ).group_by(Order.customer_id).subquery()
    
    # Получаем количество новых заказчиков по месяцам
    # Используем функции SQLite для форматирования даты
    new_customers_data = db.session.query(
        func.strftime('%Y-%m', first_orders.c.first_order_date).label('month'),
        func.count().label('count')
    ).group_by('month').order_by('month').all()
    
    # Преобразуем результаты в формат для графика
    formatted_customers_data = []
    for row in new_customers_data:
        month_str = 'Неизвестно'
        if row.month:
            try:
                month_date = datetime.strptime(str(row.month) + '-01', '%Y-%m-%d')
                month_str = month_date.strftime('%b %Y')
            except ValueError:
                month_str = str(row.month)
        
        formatted_customers_data.append({
            'month': month_str,
            'count': row.count
        })
    
    # Получаем заказчиков с повторными заказами
    repeat_customers = db.session.query(
        Customer,
        func.count(Order.id).label('orders_count'),
        func.avg(Order.total_cost).label('avg_order_value')
    ).join(Order).group_by(Customer.id).having(
        func.count(Order.id) > 1
    ).order_by(
        desc('orders_count')
    ).limit(10).all()
    
    return render_template(
        'analytics/customers.html',
        period=period,
        top_customers=top_customers,
        new_customers_data=formatted_customers_data,
        repeat_customers=repeat_customers
    ) 