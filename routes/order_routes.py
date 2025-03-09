from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Order, OrderItem, Customer, Product, Stock, Shipment, StockMovement, PriceHistory
from datetime import datetime, timedelta, timedelta
from sqlalchemy import or_, and_, desc
from utils.excel_export import export_order_details_to_excel

order_bp = Blueprint('order', __name__, url_prefix='/orders')

@order_bp.route('/')
def index():
    """Отображение списка заказов"""
    status = request.args.get('status', '')
    customer_id = request.args.get('customer_id', '')
    
    # Базовый запрос
    query = Order.query
    
    # Фильтрация по статусу
    if status:
        query = query.filter(Order.status == status)
    
    # Фильтрация по заказчику
    if customer_id and customer_id.isdigit():
        query = query.filter(Order.customer_id == int(customer_id))
    
    # Получаем заказы, отсортированные по статусу и дате создания
    orders = query.order_by(Order.status, Order.created_at.desc()).all()
    
    # Рассчитываем общую стоимость для заказов, у которых она не задана
    for order in orders:
        if order.total_cost is None:
            # Рассчитываем стоимость позиций
            items_total = sum(item.selling_price * item.quantity for item in order.items)
            
            # Добавляем стоимость доставки, если есть
            if order.customer and order.customer.delivery_fee:
                items_total += order.customer.delivery_fee
            
            order.total_cost = items_total
    
    # Получаем список заказчиков для фильтра
    customers = Customer.query.order_by(Customer.name).all()
    
    # Получаем список статусов для фильтра
    from config import Config
    statuses = Config.ORDER_STATUSES
    
    return render_template('orders/index.html', 
                          orders=orders, 
                          customers=customers, 
                          statuses=statuses,
                          selected_status=status,
                          selected_customer_id=customer_id)

@order_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Создание нового заказа"""
    # Получаем список заказчиков для выбора
    customers = Customer.query.order_by(Customer.name).all()
    
    # Если нет заказчиков, перенаправляем на страницу создания заказчика
    if not customers:
        flash('Сначала добавьте заказчика', 'warning')
        return redirect(url_for('customer.create'))
    
    # Получаем ID заказчика из параметра запроса (если есть)
    customer_id = request.args.get('customer_id')
    
    if request.method == 'POST':
        # Получаем данные из формы
        customer_id = request.form.get('customer_id')
        status = request.form.get('status')
        expected_shipping_str = request.form.get('expected_shipping')
        notes = request.form.get('notes')
        
        # Преобразуем дату отгрузки из строки в объект datetime, если она указана
        expected_shipping = None
        if expected_shipping_str and expected_shipping_str.strip():
            try:
                expected_shipping = datetime.strptime(expected_shipping_str, '%Y-%m-%d')
            except ValueError:
                flash('Неверный формат даты отгрузки', 'danger')
                return render_template('orders/create.html', customers=customers, customer_id=customer_id)
        
        # Создаем новый заказ
        order = Order(
            customer_id=customer_id,
            status=status,
            expected_shipping=expected_shipping,
            notes=notes,
            created_at=datetime.now()
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash('Заказ успешно создан', 'success')
        return redirect(url_for('order.edit', id=order.id))
    
    # Отображаем форму создания заказа
    return render_template('orders/create.html', customers=customers, customer_id=customer_id)

@order_bp.route('/view/<int:id>')
def view(id):
    """Просмотр заказа"""
    order = Order.query.get_or_404(id)
    
    # Получаем позиции заказа
    items = order.items.all()
    
    # Группируем позиции по источнику (склад/закупка)
    stock_items = [item for item in items if item.stock_id]
    product_items = [item for item in items if item.product_id]
    
    # Проверяем, изменились ли цены в прайс-листе для позиций заказа
    price_changes = {}
    for item in product_items:
        if item.product:
            # Если указана ручная цена, сравниваем с ней
            if item.custom_purchase_price:
                base_price = item.custom_purchase_price
            else:
                # Иначе рассчитываем цену из прайс-листа на момент создания заказа
                base_price = item.product.price_per_ton * (item.product.weight_per_meter / 1000)
            
            # Текущая цена из прайс-листа
            current_price = item.product.price_per_ton * (item.product.weight_per_meter / 1000)
            
            # Если цена изменилась, отмечаем это
            if abs(base_price - current_price) > 0.01:  # Учитываем погрешность вычислений
                price_changes[item.id] = {
                    'old_price': base_price,
                    'new_price': current_price,
                    'diff_percent': ((current_price - base_price) / base_price) * 100
                }
    
    return render_template('orders/view.html', 
                          order=order,
                          stock_items=stock_items,
                          product_items=product_items,
                          price_changes=price_changes)

@order_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    """Редактирование заказа"""
    order = Order.query.get_or_404(id)
    customers = Customer.query.order_by(Customer.name).all()
    
    if request.method == 'POST':
        # Получаем данные из формы
        customer_id = request.form.get('customer_id')
        status = request.form.get('status')
        expected_shipping_str = request.form.get('expected_shipping')
        notes = request.form.get('notes')
        
        # Преобразуем дату отгрузки из строки в объект datetime, если она указана
        expected_shipping = None
        if expected_shipping_str and expected_shipping_str.strip():
            try:
                expected_shipping = datetime.strptime(expected_shipping_str, '%Y-%m-%d')
            except ValueError:
                flash('Неверный формат даты отгрузки', 'danger')
                return render_template('orders/edit.html', order=order, customers=customers)
        
        # Обновляем данные заказа
        order.customer_id = customer_id
        order.status = status
        order.expected_shipping = expected_shipping
        order.notes = notes
        
        db.session.commit()
        
        flash('Заказ успешно обновлен', 'success')
        return redirect(url_for('order.view', id=order.id))
    
    # Отображаем форму редактирования заказа
    return render_template('orders/edit.html', order=order, customers=customers)

@order_bp.route('/add_item/<int:id>', methods=['GET', 'POST'])
def add_item(id):
    """Добавление позиции в заказ"""
    order = Order.query.get_or_404(id)
    
    # Если заказ уже отгружен, запрещаем добавление позиций
    if order.status == 'отгружен':
        flash('Невозможно добавить позицию в отгруженный заказ', 'danger')
        return redirect(url_for('order.view', id=id))
    
    if request.method == 'POST':
        source = request.form.get('source')  # 'stock' или 'product'
        item_id = request.form.get('item_id')
        quantity = float(request.form.get('quantity'))
        margin = float(request.form.get('margin', 0))
        custom_price = request.form.get('custom_price')  # Ручная цена для закупки
        
        # Проверяем, выбран ли товар
        if not item_id:
            flash('Необходимо выбрать товар', 'danger')
            return redirect(url_for('order.add_item', id=id))
        
        # Проверяем, указано ли количество
        if quantity <= 0:
            flash('Количество должно быть больше нуля', 'danger')
            return redirect(url_for('order.add_item', id=id))
        
        # Создаем новую позицию в заказе
        order_item = OrderItem(
            order_id=id,
            quantity=quantity,
            margin=margin
        )
        
        if source == 'stock':
            # Позиция со склада
            stock = Stock.query.get(item_id)
            
            # Проверяем, достаточно ли товара на складе
            if stock.available_quantity < quantity:
                flash(f'Недостаточно товара на складе. Доступно: {stock.available_quantity}', 'danger')
                return redirect(url_for('order.add_item', id=id))
            
            order_item.stock_id = stock.id
            order_item.purchase_price = stock.purchase_price
            
            # Рассчитываем продажную цену
            selling_price = stock.purchase_price * (1 + margin/100)
            
            # Если у заказчика есть индивидуальная маржинальность, учитываем ее
            if order.customer.margin > 0:
                selling_price *= (1 + order.customer.margin/100)
            
            order_item.selling_price = selling_price
            
            # Резервируем товар на складе
            stock.reserved_quantity += quantity
            
            # Добавляем запись о движении товара (резервирование)
            movement = StockMovement(
                stock_id=stock.id,
                order_id=order.id,
                operation_type='резервирование',
                quantity=quantity,
                purchase_price=stock.purchase_price,
                created_at=datetime.utcnow()
            )
            
            db.session.add(movement)
            
        elif source == 'product':
            # Позиция под закупку
            product = Product.query.get(item_id)
            
            order_item.product_id = product.id
            
            # Если указана ручная цена, используем ее
            if custom_price and float(custom_price) > 0:
                order_item.custom_purchase_price = float(custom_price)
                base_price = float(custom_price)
            else:
                # Иначе рассчитываем цену из прайс-листа
                base_price = product.price_per_ton * (product.weight_per_meter / 1000)
            
            # Рассчитываем продажную цену
            selling_price = base_price * (1 + margin/100)
            
            # Если у заказчика есть индивидуальная маржинальность, учитываем ее
            if order.customer.margin > 0:
                selling_price *= (1 + order.customer.margin/100)
            
            order_item.selling_price = selling_price
        
        db.session.add(order_item)
        
        # Обновляем общую стоимость заказа
        total_cost = sum(item.selling_price * item.quantity for item in order.items) + order_item.selling_price * quantity
        
        # Добавляем стоимость доставки, если есть
        if order.customer.delivery_fee > 0:
            total_cost += order.customer.delivery_fee
            
        order.total_cost = total_cost
        
        db.session.commit()
        
        flash('Позиция успешно добавлена в заказ', 'success')
        return redirect(url_for('order.edit', id=id))
    
    return render_template('orders/add_item.html', order=order)

@order_bp.route('/remove_item/<int:id>/<int:item_id>', methods=['POST'])
def remove_item(id, item_id):
    """Удаление позиции из заказа"""
    order = Order.query.get_or_404(id)
    item = OrderItem.query.get_or_404(item_id)
    
    # Проверяем, принадлежит ли позиция этому заказу
    if item.order_id != id:
        flash('Позиция не принадлежит этому заказу', 'danger')
        return redirect(url_for('order.edit', id=id))
    
    # Если заказ уже отгружен, запрещаем удаление позиций
    if order.status == 'отгружен':
        flash('Невозможно удалить позицию из отгруженного заказа', 'danger')
        return redirect(url_for('order.view', id=id))
    
    # Если позиция со склада, снимаем резервирование
    if item.stock_id:
        stock = Stock.query.get(item.stock_id)
        
        # Уменьшаем зарезервированное количество
        stock.reserved_quantity -= item.quantity
        
        # Если зарезервированное количество стало отрицательным, исправляем
        if stock.reserved_quantity < 0:
            stock.reserved_quantity = 0
        
        # Удаляем запись о движении товара (резервирование)
        StockMovement.query.filter_by(
            stock_id=item.stock_id,
            order_id=id,
            operation_type='резервирование'
        ).delete()
    
    # Удаляем позицию
    db.session.delete(item)
    
    # Обновляем общую стоимость заказа
    total_cost = sum(i.selling_price * i.quantity for i in order.items if i.id != item_id)
    
    # Добавляем стоимость доставки, если есть
    if order.customer.delivery_fee > 0:
        total_cost += order.customer.delivery_fee
        
    order.total_cost = total_cost
    
    db.session.commit()
    
    flash('Позиция успешно удалена из заказа', 'success')
    return redirect(url_for('order.edit', id=id))

@order_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Удаление заказа"""
    order = Order.query.get_or_404(id)
    
    # Если заказ уже отгружен, запрещаем удаление
    if order.status == 'отгружен':
        flash('Невозможно удалить отгруженный заказ', 'danger')
        return redirect(url_for('order.index'))
    
    # Снимаем резервирование со всех позиций со склада
    for item in order.items:
        if item.stock_id:
            stock = Stock.query.get(item.stock_id)
            
            # Уменьшаем зарезервированное количество
            stock.reserved_quantity -= item.quantity
            
            # Если зарезервированное количество стало отрицательным, исправляем
            if stock.reserved_quantity < 0:
                stock.reserved_quantity = 0
    
    # Удаляем записи о движении товара
    StockMovement.query.filter_by(order_id=id).delete()
    
    # Удаляем позиции заказа
    OrderItem.query.filter_by(order_id=id).delete()
    
    # Удаляем заказ
    db.session.delete(order)
    db.session.commit()
    
    flash('Заказ успешно удален', 'success')
    return redirect(url_for('order.index'))

@order_bp.route('/export')
def export():
    """Экспорт списка заказов в Excel"""
    # Проверяем, указан ли ID заказа
    order_id = request.args.get('id')
    
    if order_id and order_id.isdigit():
        # Если указан ID заказа, экспортируем детали этого заказа
        order = Order.query.get_or_404(int(order_id))
        output = export_order_details_to_excel(order)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"order_{order.id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    # Иначе экспортируем список всех заказов
    # Получаем параметры фильтрации
    status = request.args.get('status', '')
    customer_id = request.args.get('customer_id', '')
    
    # Базовый запрос
    query = Order.query
    
    # Фильтрация по статусу
    if status:
        query = query.filter(Order.status == status)
    
    # Фильтрация по заказчику
    if customer_id and customer_id.isdigit():
        query = query.filter(Order.customer_id == int(customer_id))
    
    # Получаем заказы, отсортированные по статусу и дате создания
    orders = query.order_by(Order.status, Order.created_at.desc()).all()
    
    # Создаем Excel-отчет
    from utils.excel_export import create_excel_report
    
    headers = ['ID', 'Заказчик', 'Дата создания', 'Статус', 'Ожидаемая отгрузка', 'Сумма (₽)', 'Примечания']
    
    data = [
        [
            order.id,
            order.customer.name if order.customer else '',
            order.created_at.strftime('%d.%m.%Y'),
            order.status,
            order.expected_shipping.strftime('%d.%m.%Y') if order.expected_shipping else '',
            order.total_cost,
            order.notes or ''
        ]
        for order in orders
    ]
    
    output = create_excel_report(
        title="Список заказов",
        headers=headers,
        data=data
    )
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f"orders_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@order_bp.route('/add_item_from_stock/<int:id>', methods=['GET', 'POST'])
def add_item_from_stock(id):
    """Добавление позиции в заказ со склада"""
    order = Order.query.get_or_404(id)
    
    # Если заказ уже отгружен, запрещаем добавление позиций
    if order.status == 'отгружен':
        flash('Невозможно добавить позицию в отгруженный заказ', 'danger')
        return redirect(url_for('order.view', id=id))
    
    if request.method == 'POST':
        stock_id = request.form.get('stock_id')
        quantity = float(request.form.get('quantity'))
        margin = float(request.form.get('margin', 0))
        
        # Проверяем, выбран ли товар
        if not stock_id:
            flash('Необходимо выбрать товар', 'danger')
            return redirect(url_for('order.add_item_from_stock', id=id))
        
        # Проверяем, указано ли количество
        if quantity <= 0:
            flash('Количество должно быть больше нуля', 'danger')
            return redirect(url_for('order.add_item_from_stock', id=id))
        
        # Получаем товар со склада
        stock = Stock.query.get(stock_id)
        
        # Проверяем, достаточно ли товара на складе
        if quantity > stock.available_quantity:
            flash(f'Недостаточно товара на складе. Доступно: {stock.available_quantity}', 'danger')
            return redirect(url_for('order.add_item_from_stock', id=id))
        
        # Создаем новую позицию в заказе
        order_item = OrderItem(
            order_id=id,
            stock_id=stock_id,
            quantity=quantity,
            purchase_price=stock.purchase_price,
            margin=margin,
            selling_price=stock.purchase_price * (1 + margin/100)
        )
        
        db.session.add(order_item)
        
        # Резервируем товар на складе
        stock.reserved_quantity += quantity
        
        # Добавляем запись о движении товара (резервирование)
        movement = StockMovement(
            stock_id=stock_id,
            order_id=id,
            operation_type='резервирование',
            quantity=quantity,
            purchase_price=stock.purchase_price,
            created_at=datetime.utcnow()
        )
        
        db.session.add(movement)
        db.session.commit()
        
        flash('Позиция успешно добавлена в заказ', 'success')
        return redirect(url_for('order.edit', id=id))
    
    # Получаем товары на складе
    # Вместо фильтрации по available_quantity, фильтруем по quantity и reserved_quantity
    stocks = Stock.query.filter(Stock.quantity > Stock.reserved_quantity).order_by(Stock.category, Stock.name).all()
    
    return render_template('orders/add_item_from_stock.html', order=order, stocks=stocks)

@order_bp.route('/add_item_from_price/<int:id>', methods=['GET', 'POST'])
def add_item_from_price(id):
    """Добавление позиции из прайс-листа в заказ"""
    order = Order.query.get_or_404(id)
    
    # Если заказ уже отгружен, запрещаем добавление позиций
    if order.status == 'отгружен':
        flash('Невозможно добавить позицию в отгруженный заказ', 'danger')
        return redirect(url_for('order.view', id=id))
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = float(request.form.get('quantity'))
        margin = float(request.form.get('margin', 0))
        custom_price = request.form.get('custom_price')
        
        # Проверяем, выбран ли товар
        if not product_id:
            flash('Необходимо выбрать товар', 'danger')
            return redirect(url_for('order.add_item_from_price', id=id))
        
        # Проверяем, указано ли количество
        if quantity <= 0:
            flash('Количество должно быть больше нуля', 'danger')
            return redirect(url_for('order.add_item_from_price', id=id))
        
        # Получаем товар из прайс-листа
        product = Product.query.get(product_id)
        
        # Если указана ручная цена, используем её
        if custom_price and float(custom_price) > 0:
            custom_price = float(custom_price)
            selling_price = custom_price * (1 + margin/100)
        else:
            # Иначе рассчитываем цену из прайс-листа
            custom_price = None
            selling_price = product.price_per_ton * (product.weight_per_meter / 1000) * (1 + margin/100)
        
        # Создаем новую позицию в заказе
        order_item = OrderItem(
            order_id=id,
            product_id=product_id,
            quantity=quantity,
            margin=margin,
            custom_purchase_price=custom_price,
            selling_price=selling_price
        )
        
        db.session.add(order_item)
        db.session.commit()
        
        flash('Позиция успешно добавлена в заказ', 'success')
        return redirect(url_for('order.edit', id=id))
    
    # Получаем товары из прайс-листа
    products = Product.query.order_by(Product.category, Product.name).all()
    
    return render_template('orders/add_item_from_price.html', order=order, products=products)

@order_bp.route('/edit_item/<int:id>/<int:item_id>', methods=['GET', 'POST'])
def edit_item(id, item_id):
    """Редактирование позиции в заказе"""
    order = Order.query.get_or_404(id)
    item = OrderItem.query.get_or_404(item_id)
    
    # Проверяем, принадлежит ли позиция этому заказу
    if item.order_id != id:
        flash('Позиция не найдена в этом заказе', 'danger')
        return redirect(url_for('order.edit', id=id))
    
    # Если заказ уже отгружен, запрещаем редактирование позиций
    if order.status == 'отгружен':
        flash('Невозможно редактировать позицию в отгруженном заказе', 'danger')
        return redirect(url_for('order.view', id=id))
    
    if request.method == 'POST':
        quantity = float(request.form.get('quantity'))
        margin = float(request.form.get('margin', 0))
        
        # Проверяем, указано ли количество
        if quantity <= 0:
            flash('Количество должно быть больше нуля', 'danger')
            return redirect(url_for('order.edit_item', id=id, item_id=item_id))
        
        # Если позиция со склада, проверяем доступность
        if item.stock_id:
            stock = Stock.query.get(item.stock_id)
            
            # Рассчитываем, сколько нужно дополнительно зарезервировать
            additional = quantity - item.quantity
            
            # Если нужно увеличить количество, проверяем доступность
            if additional > 0 and additional > stock.available_quantity:
                flash(f'Недостаточно товара на складе. Доступно: {stock.available_quantity}', 'danger')
                return redirect(url_for('order.edit_item', id=id, item_id=item_id))
            
            # Обновляем резервирование на складе
            stock.reserved_quantity += additional
            
            # Если количество изменилось, добавляем запись о движении товара
            if additional != 0:
                operation_type = 'резервирование' if additional > 0 else 'отмена резервирования'
                
                movement = StockMovement(
                    stock_id=stock.id,
                    order_id=id,
                    operation_type=operation_type,
                    quantity=abs(additional),
                    purchase_price=stock.purchase_price,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(movement)
            
            # Обновляем цену продажи
            item.selling_price = stock.purchase_price * (1 + margin/100)
        elif item.product_id:
            # Если позиция из прайс-листа
            product = Product.query.get(item.product_id)
            
            # Если указана ручная цена, используем её
            custom_price = request.form.get('custom_price')
            if custom_price and float(custom_price) > 0:
                custom_price = float(custom_price)
                item.custom_purchase_price = custom_price
                item.selling_price = custom_price * (1 + margin/100)
            else:
                # Иначе рассчитываем цену из прайс-листа
                item.custom_purchase_price = None
                item.selling_price = product.price_per_ton * (product.weight_per_meter / 1000) * (1 + margin/100)
        
        # Обновляем данные позиции
        item.quantity = quantity
        item.margin = margin
        
        db.session.commit()
        
        flash('Позиция успешно обновлена', 'success')
        return redirect(url_for('order.edit', id=id))
    
    return render_template('orders/edit_item.html', order=order, item=item)

@order_bp.route('/delete_item/<int:id>/<int:item_id>', methods=['POST'])
def delete_item(id, item_id):
    """Удаление позиции из заказа"""
    order = Order.query.get_or_404(id)
    item = OrderItem.query.get_or_404(item_id)
    
    # Проверяем, принадлежит ли позиция этому заказу
    if item.order_id != id:
        flash('Позиция не найдена в этом заказе', 'danger')
        return redirect(url_for('order.edit', id=id))
    
    # Если заказ уже отгружен, запрещаем удаление позиций
    if order.status == 'отгружен':
        flash('Невозможно удалить позицию из отгруженного заказа', 'danger')
        return redirect(url_for('order.view', id=id))
    
    # Если позиция со склада, снимаем резервирование
    if item.stock_id:
        stock = Stock.query.get(item.stock_id)
        
        # Уменьшаем зарезервированное количество
        stock.reserved_quantity -= item.quantity
        
        # Если зарезервированное количество стало отрицательным, исправляем
        if stock.reserved_quantity < 0:
            stock.reserved_quantity = 0
        
        # Добавляем запись о движении товара (отмена резервирования)
        movement = StockMovement(
            stock_id=stock.id,
            order_id=id,
            operation_type='отмена резервирования',
            quantity=item.quantity,
            purchase_price=stock.purchase_price,
            created_at=datetime.utcnow()
        )
        
        db.session.add(movement)
    
    # Удаляем позицию
    db.session.delete(item)
    db.session.commit()
    
    flash('Позиция успешно удалена из заказа', 'success')
    return redirect(url_for('order.edit', id=id)) 