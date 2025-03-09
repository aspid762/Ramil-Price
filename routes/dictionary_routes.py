from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Dictionary
from datetime import datetime
from sqlalchemy import desc

dictionary_bp = Blueprint('dictionary', __name__, url_prefix='/dictionaries')

@dictionary_bp.route('/')
def index():
    """Отображение списка справочников"""
    # Получаем уникальные типы справочников
    dictionary_types = db.session.query(Dictionary.type).distinct().all()
    dictionary_types = [t[0] for t in dictionary_types]
    
    # Добавляем стандартные типы, если их нет в базе
    standard_types = ['product_categories', 'order_statuses', 'stock_operation_types']
    for type_name in standard_types:
        if type_name not in dictionary_types:
            dictionary_types.append(type_name)
    
    # Получаем количество записей для каждого типа
    type_counts = {}
    for type_name in dictionary_types:
        count = Dictionary.query.filter_by(type=type_name).count()
        type_counts[type_name] = count
    
    return render_template('dictionaries/index.html', 
                          dictionary_types=dictionary_types,
                          type_counts=type_counts)

@dictionary_bp.route('/<string:type>')
def view_type(type):
    """Отображение значений конкретного справочника"""
    # Получаем все значения справочника, отсортированные по порядку сортировки и названию
    values = Dictionary.query.filter_by(type=type).order_by(Dictionary.sort_order, Dictionary.name).all()
    
    # Определяем заголовок справочника
    type_titles = {
        'product_categories': 'Категории товаров',
        'order_statuses': 'Статусы заказов',
        'stock_operation_types': 'Типы операций со складом'
    }
    
    title = type_titles.get(type, type.replace('_', ' ').title())
    
    return render_template('dictionaries/view_type.html', 
                          type=type,
                          title=title,
                          values=values)

@dictionary_bp.route('/<string:type>/create', methods=['GET', 'POST'])
def create(type):
    """Создание нового значения в справочнике"""
    # Определяем заголовок справочника
    type_titles = {
        'product_categories': 'Категории товаров',
        'order_statuses': 'Статусы заказов',
        'stock_operation_types': 'Типы операций со складом'
    }
    
    title = type_titles.get(type, type.replace('_', ' ').title())
    
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        sort_order = request.form.get('sort_order', 0)
        
        # Проверяем, что код и название не пустые
        if not code or not name:
            flash('Код и название не могут быть пустыми', 'danger')
            return render_template('dictionaries/create.html', type=type, title=title)
        
        # Проверяем, что код уникален для данного типа справочника
        existing = Dictionary.query.filter_by(type=type, code=code).first()
        if existing:
            flash(f'Значение с кодом "{code}" уже существует в справочнике', 'danger')
            return render_template('dictionaries/create.html', type=type, title=title)
        
        # Создаем новое значение
        value = Dictionary(
            type=type,
            code=code,
            name=name,
            sort_order=int(sort_order) if sort_order else 0,
            is_active=True
        )
        
        db.session.add(value)
        db.session.commit()
        
        flash('Значение успешно добавлено в справочник', 'success')
        return redirect(url_for('dictionary.view_type', type=type))
    
    return render_template('dictionaries/create.html', type=type, title=title)

@dictionary_bp.route('/<string:type>/edit/<int:id>', methods=['GET', 'POST'])
def edit(type, id):
    """Редактирование значения в справочнике"""
    # Получаем значение из базы
    value = Dictionary.query.get_or_404(id)
    
    # Проверяем, что значение принадлежит указанному типу справочника
    if value.type != type:
        flash('Значение не найдено в указанном справочнике', 'danger')
        return redirect(url_for('dictionary.view_type', type=type))
    
    # Определяем заголовок справочника
    type_titles = {
        'product_categories': 'Категории товаров',
        'order_statuses': 'Статусы заказов',
        'stock_operation_types': 'Типы операций со складом'
    }
    
    title = type_titles.get(type, type.replace('_', ' ').title())
    
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        sort_order = request.form.get('sort_order', 0)
        is_active = 'is_active' in request.form
        
        # Проверяем, что код и название не пустые
        if not code or not name:
            flash('Код и название не могут быть пустыми', 'danger')
            return render_template('dictionaries/edit.html', type=type, title=title, value=value)
        
        # Проверяем, что код уникален для данного типа справочника (исключая текущее значение)
        existing = Dictionary.query.filter(Dictionary.type == type, 
                                          Dictionary.code == code, 
                                          Dictionary.id != id).first()
        if existing:
            flash(f'Значение с кодом "{code}" уже существует в справочнике', 'danger')
            return render_template('dictionaries/edit.html', type=type, title=title, value=value)
        
        # Обновляем значение
        value.code = code
        value.name = name
        value.sort_order = int(sort_order) if sort_order else 0
        value.is_active = is_active
        value.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Значение успешно обновлено', 'success')
        return redirect(url_for('dictionary.view_type', type=type))
    
    return render_template('dictionaries/edit.html', type=type, title=title, value=value)

@dictionary_bp.route('/<string:type>/delete/<int:id>', methods=['POST'])
def delete(type, id):
    """Удаление значения из справочника"""
    # Получаем значение из базы
    value = Dictionary.query.get_or_404(id)
    
    # Проверяем, что значение принадлежит указанному типу справочника
    if value.type != type:
        flash('Значение не найдено в указанном справочнике', 'danger')
        return redirect(url_for('dictionary.view_type', type=type))
    
    # Проверяем, используется ли значение в других таблицах
    # Это зависит от конкретной реализации и связей в базе данных
    # Здесь нужно добавить проверки для каждого типа справочника
    
    # Удаляем значение
    db.session.delete(value)
    db.session.commit()
    
    flash('Значение успешно удалено из справочника', 'success')
    return redirect(url_for('dictionary.view_type', type=type))

@dictionary_bp.route('/api/<string:type>')
def api_get_values(type):
    """API для получения значений справочника"""
    values = Dictionary.query.filter_by(type=type, is_active=True).order_by(Dictionary.sort_order, Dictionary.name).all()
    
    result = []
    for value in values:
        result.append({
            'id': value.id,
            'code': value.code,
            'name': value.name,
            'sort_order': value.sort_order
        })
    
    return jsonify(result) 