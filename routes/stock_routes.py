from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Stock, StockMovement, Product
from datetime import datetime, timedelta, timedelta
from sqlalchemy import or_

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')

@stock_bp.route('/')
def index():
    """Отображение списка товаров на складе"""
    search = request.args.get('search', '')
    
    # Фильтрация по поисковому запросу
    if search:
        stocks = Stock.query.filter(
            or_(
                Stock.category.ilike(f'%{search}%'),
                Stock.name.ilike(f'%{search}%'),
                Stock.characteristics.ilike(f'%{search}%')
            )
        ).order_by(Stock.category, Stock.name, Stock.received_at.desc()).all()
    else:
        stocks = Stock.query.order_by(Stock.category, Stock.name, Stock.received_at.desc()).all()
    
    return render_template('stock/index.html', stocks=stocks, search=search)

@stock_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Добавление новой партии на склад"""
    from config import Config
    
    if request.method == 'POST':
        category = request.form.get('category')
        name = request.form.get('name')
        characteristics = request.form.get('characteristics')
        quantity = float(request.form.get('quantity'))
        purchase_price = float(request.form.get('purchase_price'))
        
        # Создаем новую партию на складе
        stock = Stock(
            category=category,
            name=name,
            characteristics=characteristics,
            quantity=quantity,
            purchase_price=purchase_price,
            received_at=datetime.utcnow()
        )
        
        db.session.add(stock)
        db.session.commit()
        
        # Добавляем запись о движении товара (поступление)
        movement = StockMovement(
            stock_id=stock.id,
            operation_type='поступление',
            quantity=quantity,
            purchase_price=purchase_price,
            created_at=datetime.utcnow()
        )
        
        db.session.add(movement)
        db.session.commit()
        
        flash('Партия успешно добавлена на склад', 'success')
        return redirect(url_for('stock.index'))
    
    return render_template('stock/create.html', categories=Config.PRODUCT_CATEGORIES)

@stock_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    """Редактирование позиции на складе"""
    stock = Stock.query.get_or_404(id)
    
    if request.method == 'POST':
        # Получаем данные из формы
        category = request.form.get('category')
        name = request.form.get('name')
        characteristics = request.form.get('characteristics')
        quantity = float(request.form.get('quantity'))
        purchase_price = float(request.form.get('purchase_price'))
        
        # Обновляем данные
        stock.category = category
        stock.name = name
        stock.characteristics = characteristics
        
        # Если количество изменилось, добавляем запись о движении товара
        if quantity != stock.quantity:
            # Рассчитываем разницу
            diff = quantity - stock.quantity
            
            # Определяем тип операции
            operation_type = 'поступление' if diff > 0 else 'списание'
            
            # Добавляем запись о движении товара
            movement = StockMovement(
                stock_id=id,
                operation_type=operation_type,
                quantity=abs(diff),
                purchase_price=purchase_price,
                created_at=datetime.utcnow()
            )
            db.session.add(movement)
            
            # Обновляем количество
            stock.quantity = quantity
        
        # Если цена изменилась, обновляем её
        if purchase_price != stock.purchase_price:
            stock.purchase_price = purchase_price
        
        db.session.commit()
        
        flash('Позиция на складе успешно обновлена', 'success')
        return redirect(url_for('stock.index'))
    
    return render_template('stock/edit.html', stock=stock)

@stock_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Удаление позиции со склада"""
    stock = Stock.query.get_or_404(id)
    
    # Проверяем, есть ли зарезервированное количество
    if stock.reserved_quantity > 0:
        flash('Невозможно удалить позицию, так как часть товара зарезервирована', 'danger')
        return redirect(url_for('stock.index'))
    
    # Удаляем записи о движении товара
    StockMovement.query.filter_by(stock_id=id).delete()
    
    # Удаляем позицию со склада
    db.session.delete(stock)
    db.session.commit()
    
    flash('Позиция успешно удалена со склада', 'success')
    return redirect(url_for('stock.index'))

@stock_bp.route('/api/search')
def api_search():
    """API для поиска товаров на складе (используется в AJAX-запросах)"""
    search = request.args.get('q', '')
    
    if search:
        stocks = Stock.query.filter(
            or_(
                Stock.category.ilike(f'%{search}%'),
                Stock.name.ilike(f'%{search}%'),
                Stock.characteristics.ilike(f'%{search}%')
            )
        ).order_by(Stock.category, Stock.name, Stock.received_at.desc()).all()
    else:
        stocks = []
    
    result = []
    for stock in stocks:
        result.append({
            'id': stock.id,
            'category': stock.category,
            'name': stock.name,
            'characteristics': stock.characteristics,
            'quantity': stock.quantity,
            'available_quantity': stock.available_quantity,
            'reserved_quantity': stock.reserved_quantity,
            'purchase_price': stock.purchase_price,
            'received_at': stock.received_at.strftime('%d.%m.%Y')
        })
    
    return jsonify(result)

@stock_bp.route('/view/<int:id>')
def view(id):
    """Просмотр позиции на складе"""
    stock = Stock.query.get_or_404(id)
    
    # Получаем историю движения товара
    movements = StockMovement.query.filter_by(stock_id=id).order_by(StockMovement.created_at.desc()).all()
    
    return render_template('stock/view.html', stock=stock, movements=movements)

@stock_bp.route('/export')
def export():
    """Экспорт списка товаров на складе в Excel"""
    stock_items = Stock.query.order_by(Stock.category, Stock.name).all()
    output = export_stock_to_excel(stock_items)
    return send_file(
        output,
        as_attachment=True,
        download_name=f"stock_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@stock_bp.route('/import', methods=['GET', 'POST'])
def import_stock():
    """Импорт товаров на склад из Excel-файла"""
    if request.method == 'POST':
        # Проверяем, что файл был загружен
        if 'file' not in request.files:
            flash('Файл не выбран', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Проверяем, что имя файла не пустое
        if file.filename == '':
            flash('Файл не выбран', 'danger')
            return redirect(request.url)
        
        # Проверяем расширение файла
        if not file.filename.endswith('.xlsx'):
            flash('Файл должен быть в формате Excel (.xlsx)', 'danger')
            return redirect(request.url)
        
        # Сохраняем файл во временную директорию
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        
        # Импортируем данные
        from utils.excel_import import import_stock_from_excel
        result = import_stock_from_excel(file_path)
        
        # Удаляем временный файл
        os.remove(file_path)
        
        if result['success']:
            flash(f'Импорт завершен: добавлено {result["imported"]} позиций на склад', 'success')
            
            # Если есть ошибки, выводим их
            if result['errors']:
                for error in result['errors']:
                    flash(error, 'warning')
        else:
            flash(f'Ошибка при импорте: {result["error"]}', 'danger')
            
            # Выводим детальные ошибки
            for error in result['errors']:
                flash(error, 'warning')
        
        return redirect(url_for('stock.index'))
    
    # Отображаем форму для загрузки файла
    return render_template('stock/import.html') 