from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from models import db, Customer, Order
from sqlalchemy import or_
from datetime import datetime, timedelta, timedelta

customer_bp = Blueprint('customer', __name__, url_prefix='/customers')

@customer_bp.route('/')
def index():
    """Отображение списка заказчиков"""
    search = request.args.get('search', '')
    
    # Фильтрация по поисковому запросу
    if search:
        customers = Customer.query.filter(
            or_(
                Customer.name.ilike(f'%{search}%'),
                Customer.phone.ilike(f'%{search}%'),
                Customer.address.ilike(f'%{search}%')
            )
        ).order_by(Customer.name).all()
    else:
        customers = Customer.query.order_by(Customer.name).all()
    
    return render_template('customers/index.html', customers=customers, search=search)

@customer_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Создание нового заказчика"""
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        margin = request.form.get('margin', 0)
        delivery_fee = request.form.get('delivery_fee', 0)
        
        # Преобразование пустых строк в нули
        if not margin:
            margin = 0
        if not delivery_fee:
            delivery_fee = 0
        
        customer = Customer(
            name=name,
            phone=phone,
            address=address,
            margin=float(margin),
            delivery_fee=float(delivery_fee)
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash('Заказчик успешно добавлен', 'success')
        return redirect(url_for('customer.index'))
    
    return render_template('customers/create.html')

@customer_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    """Редактирование заказчика"""
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.phone = request.form.get('phone')
        customer.address = request.form.get('address')
        
        margin = request.form.get('margin', 0)
        delivery_fee = request.form.get('delivery_fee', 0)
        
        # Преобразование пустых строк в нули
        if not margin:
            margin = 0
        if not delivery_fee:
            delivery_fee = 0
            
        customer.margin = float(margin)
        customer.delivery_fee = float(delivery_fee)
        
        db.session.commit()
        
        flash('Данные заказчика успешно обновлены', 'success')
        return redirect(url_for('customer.index'))
    
    return render_template('customers/edit.html', customer=customer)

@customer_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Удаление заказчика"""
    customer = Customer.query.get_or_404(id)
    
    # Проверяем, есть ли у заказчика заказы
    if customer.orders.count() > 0:
        flash('Невозможно удалить заказчика, так как у него есть заказы', 'danger')
        return redirect(url_for('customer.index'))
    
    db.session.delete(customer)
    db.session.commit()
    
    flash('Заказчик успешно удален', 'success')
    return redirect(url_for('customer.index'))

@customer_bp.route('/view/<int:id>')
def view(id):
    """Просмотр информации о заказчике"""
    customer = Customer.query.get_or_404(id)
    
    # Получаем заказы заказчика
    orders = Order.query.filter_by(customer_id=id).order_by(Order.created_at.desc()).all()
    
    return render_template('customers/view.html', customer=customer, orders=orders)

@customer_bp.route('/export')
def export():
    """Экспорт списка заказчиков в Excel"""
    customers = Customer.query.order_by(Customer.name).all()
    output = export_customers_to_excel(customers)
    return send_file(
        output,
        as_attachment=True,
        download_name=f"customers_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@customer_bp.route('/import', methods=['GET', 'POST'])
def import_customers():
    """Импорт заказчиков из Excel-файла"""
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
        from utils.excel_import import import_customers_from_excel
        result = import_customers_from_excel(file_path)
        
        # Удаляем временный файл
        os.remove(file_path)
        
        if result['success']:
            flash(f'Импорт завершен: добавлено {result["imported"]} заказчиков, обновлено {result["updated"]} заказчиков', 'success')
            
            # Если есть ошибки, выводим их
            if result['errors']:
                for error in result['errors']:
                    flash(error, 'warning')
        else:
            flash(f'Ошибка при импорте: {result["error"]}', 'danger')
            
            # Выводим детальные ошибки
            for error in result['errors']:
                flash(error, 'warning')
        
        return redirect(url_for('customer.index'))
    
    # Отображаем форму для загрузки файла
    return render_template('customers/import.html') 