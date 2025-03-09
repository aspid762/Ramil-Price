from flask import Blueprint, render_template, request
from models import Product, Customer, Order, Stock
from sqlalchemy import or_

search_bp = Blueprint('search', __name__)

@search_bp.route('/')
def index():
    """Глобальный поиск по приложению"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 3:
        return render_template('search/index.html', query=query, results=None)
    
    # Поиск по товарам
    products = Product.query.filter(
        or_(
            Product.category.ilike(f'%{query}%'),
            Product.name.ilike(f'%{query}%'),
            Product.characteristics.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    # Поиск по заказчикам
    customers = Customer.query.filter(
        or_(
            Customer.name.ilike(f'%{query}%'),
            Customer.phone.ilike(f'%{query}%'),
            Customer.address.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    # Поиск по заказам
    orders = Order.query.filter(
        or_(
            Order.id.in_([int(query) for _ in [1] if query.isdigit()]),
            Order.status.ilike(f'%{query}%'),
            Order.notes.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    # Поиск по складу
    stock_items = Stock.query.filter(
        or_(
            Stock.category.ilike(f'%{query}%'),
            Stock.name.ilike(f'%{query}%'),
            Stock.characteristics.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = {
        'products': products,
        'customers': customers,
        'orders': orders,
        'stock_items': stock_items
    }
    
    return render_template('search/index.html', query=query, results=results) 