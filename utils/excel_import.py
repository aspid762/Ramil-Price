import openpyxl
from models import db, Product, Customer, Stock
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger('excel_import')

def import_products_from_excel(file_path):
    """Импортирует товары из Excel-файла."""
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    # Пропускаем заголовок
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    
    imported_count = 0
    updated_count = 0
    errors = []
    
    for row in rows:
        try:
            # Проверяем, что строка не пустая
            if not row[0]:
                continue
            
            category = row[0]
            name = row[1]
            characteristics = row[2]
            price_per_ton = float(row[3])
            weight_per_meter = float(row[4])
            
            # Проверяем, существует ли уже такой товар
            existing_product = Product.query.filter_by(
                category=category,
                name=name,
                characteristics=characteristics
            ).first()
            
            if existing_product:
                # Обновляем существующий товар
                existing_product.price_per_ton = price_per_ton
                existing_product.weight_per_meter = weight_per_meter
                updated_count += 1
            else:
                # Создаем новый товар
                product = Product(
                    category=category,
                    name=name,
                    characteristics=characteristics,
                    price_per_ton=price_per_ton,
                    weight_per_meter=weight_per_meter
                )
                db.session.add(product)
                imported_count += 1
        except Exception as e:
            errors.append(f"Ошибка в строке {rows.index(row) + 2}: {str(e)}")
    
    try:
        db.session.commit()
        return {
            'success': True,
            'imported': imported_count,
            'updated': updated_count,
            'errors': errors
        }
    except SQLAlchemyError as e:
        db.session.rollback()
        return {
            'success': False,
            'error': str(e),
            'errors': errors
        }

def import_customers_from_excel(file_path):
    """Импортирует заказчиков из Excel-файла."""
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    # Пропускаем заголовок
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    
    imported_count = 0
    updated_count = 0
    errors = []
    
    for row in rows:
        try:
            # Проверяем, что строка не пустая
            if not row[0]:
                continue
            
            name = row[0]
            phone = row[1] if row[1] else ''
            address = row[2] if row[2] else ''
            margin = float(row[3]) if row[3] else 0.0
            delivery_fee = float(row[4]) if row[4] else 0.0
            
            # Проверяем, существует ли уже такой заказчик
            existing_customer = Customer.query.filter_by(name=name).first()
            
            if existing_customer:
                # Обновляем существующего заказчика
                existing_customer.phone = phone
                existing_customer.address = address
                existing_customer.margin = margin
                existing_customer.delivery_fee = delivery_fee
                updated_count += 1
            else:
                # Создаем нового заказчика
                customer = Customer(
                    name=name,
                    phone=phone,
                    address=address,
                    margin=margin,
                    delivery_fee=delivery_fee
                )
                db.session.add(customer)
                imported_count += 1
        except Exception as e:
            errors.append(f"Ошибка в строке {rows.index(row) + 2}: {str(e)}")
    
    try:
        db.session.commit()
        return {
            'success': True,
            'imported': imported_count,
            'updated': updated_count,
            'errors': errors
        }
    except SQLAlchemyError as e:
        db.session.rollback()
        return {
            'success': False,
            'error': str(e),
            'errors': errors
        }

def import_stock_from_excel(file_path):
    """Импортирует товары на склад из Excel-файла."""
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    # Пропускаем заголовок
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    
    imported_count = 0
    updated_count = 0
    errors = []
    
    for row in rows:
        try:
            # Проверяем, что строка не пустая
            if not row[0]:
                continue
            
            category = row[0]
            name = row[1]
            characteristics = row[2]
            quantity = float(row[3])
            purchase_price = float(row[4])
            
            # Создаем новую позицию на складе
            stock = Stock(
                category=category,
                name=name,
                characteristics=characteristics,
                quantity=quantity,
                reserved_quantity=0.0,
                purchase_price=purchase_price,
                received_at=datetime.now()
            )
            db.session.add(stock)
            imported_count += 1
            
            # Добавляем запись о движении товара
            from models import StockMovement
            movement = StockMovement(
                stock_id=stock.id,
                operation_type='поступление',
                quantity=quantity,
                purchase_price=purchase_price,
                created_at=datetime.now()
            )
            db.session.add(movement)
        except Exception as e:
            errors.append(f"Ошибка в строке {rows.index(row) + 2}: {str(e)}")
    
    try:
        db.session.commit()
        return {
            'success': True,
            'imported': imported_count,
            'updated': updated_count,
            'errors': errors
        }
    except SQLAlchemyError as e:
        db.session.rollback()
        return {
            'success': False,
            'error': str(e),
            'errors': errors
        } 