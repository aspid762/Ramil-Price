from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Product, PriceHistory
from datetime import datetime, timedelta, timedelta
from sqlalchemy import or_
from utils.excel_export import export_products_to_excel

product_bp = Blueprint('product', __name__, url_prefix='/products')

@product_bp.route('/')
def index():
    """Отображение списка товаров"""
    search = request.args.get('search', '')
    
    # Базовый запрос
    query = Product.query
    
    # Фильтрация по поисковому запросу
    if search:
        # Разбиваем поисковый запрос на отдельные слова
        search_terms = search.split()
        
        # Создаем условия для поиска по каждому слову
        conditions = []
        for term in search_terms:
            term_like = f'%{term}%'
            condition = or_(
                Product.category.ilike(term_like),
                Product.name.ilike(term_like),
                Product.characteristics.ilike(term_like)
            )
            conditions.append(condition)
        
        # Применяем все условия (AND между разными словами)
        for condition in conditions:
            query = query.filter(condition)
    
    # Получаем отфильтрованные товары
    products = query.order_by(Product.category, Product.name).all()
    
    # Получаем все товары для интерактивного поиска
    all_products = Product.query.order_by(Product.category, Product.name).all()
    
    return render_template('products/index.html', 
                          products=products, 
                          all_products=all_products,
                          search=search)

@product_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Создание новой позиции в прайс-листе"""
    from config import Config
    
    if request.method == 'POST':
        category = request.form.get('category')
        name = request.form.get('name')
        characteristics = request.form.get('characteristics')
        price_per_ton = float(request.form.get('price_per_ton'))
        weight_per_meter = float(request.form.get('weight_per_meter'))
        
        product = Product(
            category=category,
            name=name,
            characteristics=characteristics,
            price_per_ton=price_per_ton,
            weight_per_meter=weight_per_meter
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Позиция успешно добавлена в прайс-лист', 'success')
        return redirect(url_for('product.index'))
    
    return render_template('products/create.html', categories=Config.PRODUCT_CATEGORIES)

@product_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    """Редактирование позиции в прайс-листе"""
    from config import Config
    
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        # Сохраняем старую цену в историю, если она изменилась
        new_price_per_ton = float(request.form.get('price_per_ton'))
        
        if product.price_per_ton != new_price_per_ton:
            price_history = PriceHistory(
                product_id=product.id,
                price_per_ton=product.price_per_ton,
                created_at=datetime.utcnow()
            )
            db.session.add(price_history)
        
        # Обновляем данные продукта
        product.category = request.form.get('category')
        product.name = request.form.get('name')
        product.characteristics = request.form.get('characteristics')
        product.price_per_ton = new_price_per_ton
        product.weight_per_meter = float(request.form.get('weight_per_meter'))
        
        db.session.commit()
        
        flash('Позиция успешно обновлена', 'success')
        return redirect(url_for('product.index'))
    
    return render_template('products/edit.html', product=product, categories=Config.PRODUCT_CATEGORIES)

@product_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Удаление позиции из прайс-листа"""
    product = Product.query.get_or_404(id)
    
    # Проверяем, используется ли продукт в заказах
    if product.order_items.count() > 0:
        flash('Невозможно удалить позицию, так как она используется в заказах', 'danger')
        return redirect(url_for('product.index'))
    
    # Удаляем историю цен
    PriceHistory.query.filter_by(product_id=id).delete()
    
    # Удаляем продукт
    db.session.delete(product)
    db.session.commit()
    
    flash('Позиция успешно удалена из прайс-листа', 'success')
    return redirect(url_for('product.index'))

@product_bp.route('/history/<int:id>')
def history(id):
    """Просмотр истории изменения цен товара"""
    product = Product.query.get_or_404(id)
    
    # Получаем историю изменения цен, отсортированную по дате (от новых к старым)
    # Заменяем PriceHistory.changed_at на PriceHistory.created_at
    history = PriceHistory.query.filter_by(product_id=id).order_by(PriceHistory.created_at.desc()).all()
    
    return render_template('products/history.html', product=product, history=history)

@product_bp.route('/api/search')
def api_search():
    """API для поиска продуктов (используется в AJAX-запросах)"""
    search = request.args.get('q', '')
    
    if search:
        products = Product.query.filter(
            or_(
                Product.category.ilike(f'%{search}%'),
                Product.name.ilike(f'%{search}%'),
                Product.characteristics.ilike(f'%{search}%')
            )
        ).order_by(Product.category, Product.name).all()
    else:
        products = []
    
    result = []
    for product in products:
        result.append({
            'id': product.id,
            'category': product.category,
            'name': product.name,
            'characteristics': product.characteristics,
            'price_per_ton': product.price_per_ton,
            'weight_per_meter': product.weight_per_meter,
            'price_per_meter': product.price_per_meter
        })
    
    return jsonify(result)

@product_bp.route('/export')
def export():
    """Экспорт прайс-листа в Excel"""
    products = Product.query.order_by(Product.category, Product.name).all()
    output = export_products_to_excel(products)
    return send_file(
        output,
        as_attachment=True,
        download_name=f"price_list_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@product_bp.route('/import', methods=['GET', 'POST'])
def import_products():
    """Импорт товаров из Excel-файла"""
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
        from utils.excel_import import import_products_from_excel
        result = import_products_from_excel(file_path)
        
        # Удаляем временный файл
        os.remove(file_path)
        
        if result['success']:
            flash(f'Импорт завершен: добавлено {result["imported"]} товаров, обновлено {result["updated"]} товаров', 'success')
            
            # Если есть ошибки, выводим их
            if result['errors']:
                for error in result['errors']:
                    flash(error, 'warning')
        else:
            flash(f'Ошибка при импорте: {result["error"]}', 'danger')
            
            # Выводим детальные ошибки
            for error in result['errors']:
                flash(error, 'warning')
        
        return redirect(url_for('product.index'))
    
    # Отображаем форму для загрузки файла
    return render_template('products/import.html') 