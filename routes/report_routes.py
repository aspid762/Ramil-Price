from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from models import db, Stock, StockMovement, Order, OrderItem, Product, PriceHistory
from datetime import datetime, timedelta, timedelta
from sqlalchemy import func
import calendar
from utils.excel_export import export_stock_movements_to_excel, create_excel_report

report_bp = Blueprint('report', __name__, url_prefix='/reports')

@report_bp.route('/')
def index():
    """Главная страница отчетов"""
    return render_template('reports/index.html')

@report_bp.route('/stock-movements')
def stock_movements():
    """Отчет о движении товаров на складе"""
    # Получаем параметры фильтрации
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    operation_type = request.args.get('operation_type', '')
    
    # Преобразуем строки дат в объекты datetime
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Неверный формат начальной даты', 'danger')
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Устанавливаем конец дня
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            flash('Неверный формат конечной даты', 'danger')
    
    # Если даты не указаны, устанавливаем период за последний месяц
    if not start_date and not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    
    # Формируем запрос с учетом фильтров
    query = StockMovement.query.filter(
        StockMovement.created_at >= start_date,
        StockMovement.created_at <= end_date
    )
    
    if operation_type:
        query = query.filter(StockMovement.operation_type == operation_type)
    
    # Получаем движения товаров, отсортированные по дате (от новых к старым)
    movements = query.order_by(StockMovement.created_at.desc()).all()
    
    # Получаем список типов операций для фильтра
    operation_types = db.session.query(StockMovement.operation_type).distinct().all()
    operation_types = [op[0] for op in operation_types]
    
    return render_template(
        'reports/stock_movements.html',
        movements=movements,
        start_date=start_date,
        end_date=end_date,
        operation_type=operation_type,
        operation_types=operation_types
    )

@report_bp.route('/stock-movements/export')
def export_stock_movements():
    """Экспорт отчета о движении товаров на складе в Excel"""
    # Получаем параметры фильтрации
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    operation_type = request.args.get('operation_type', '')
    
    # Преобразуем строки дат в объекты datetime
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Неверный формат начальной даты', 'danger')
            return redirect(url_for('report.stock_movements'))
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Устанавливаем конец дня
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            flash('Неверный формат конечной даты', 'danger')
            return redirect(url_for('report.stock_movements'))
    
    # Если даты не указаны, устанавливаем период за последний месяц
    if not start_date and not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    
    # Формируем запрос с учетом фильтров
    query = StockMovement.query.filter(
        StockMovement.created_at >= start_date,
        StockMovement.created_at <= end_date
    )
    
    if operation_type:
        query = query.filter(StockMovement.operation_type == operation_type)
    
    # Получаем движения товаров, отсортированные по дате (от новых к старым)
    movements = query.order_by(StockMovement.created_at.desc()).all()
    
    # Экспортируем в Excel
    output = export_stock_movements_to_excel(movements, start_date, end_date)
    
    # Формируем имя файла
    filename = f"stock_movements_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@report_bp.route('/price_history')
def price_history():
    """Отчет по истории изменения цен"""
    # Получаем ID выбранного продукта
    product_id = request.args.get('product_id', '')
    
    # Получаем все продукты для выпадающего списка
    products = Product.query.order_by(Product.category, Product.name).all()
    
    selected_product = None
    price_history = []
    
    if product_id and product_id.isdigit():
        # Получаем выбранный продукт
        selected_product = Product.query.get_or_404(int(product_id))
        
        # Получаем историю цен для выбранного продукта
        price_history = PriceHistory.query.filter_by(product_id=int(product_id)).order_by(PriceHistory.created_at.desc()).all()
    
    return render_template(
        'reports/price_history.html',
        products=products,
        selected_product=selected_product,
        price_history=price_history
    )

@report_bp.route('/price_history/export')
def export_price_history():
    """Экспорт истории цен в Excel"""
    # Получаем ID продукта
    product_id = request.args.get('product_id', '')
    
    if not product_id or not product_id.isdigit():
        flash('Не указан ID продукта', 'danger')
        return redirect(url_for('report.price_history'))
    
    # Получаем продукт
    product = Product.query.get_or_404(int(product_id))
    
    # Получаем историю цен
    price_history = PriceHistory.query.filter_by(product_id=int(product_id)).order_by(PriceHistory.created_at.desc()).all()
    
    # Подготавливаем данные для Excel
    title = f"История цен: {product.category} {product.name}"
    headers = ["Дата изменения", "Цена за тонну (₽)", "Цена за метр (₽)"]
    
    data = [
        [
            "Текущая цена",
            product.price_per_ton,
            product.price_per_meter
        ]
    ]
    
    for history in price_history:
        data.append([
            history.created_at.strftime('%d.%m.%Y %H:%M'),
            history.price_per_ton,
            history.price_per_ton * product.weight_per_meter / 1000
        ])
    
    # Экспортируем в Excel
    output = create_excel_report(title, headers, data)
    
    # Формируем имя файла
    filename = f"price_history_{product.category}_{product.name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ) 