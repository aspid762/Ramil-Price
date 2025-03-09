"""
Скрипт для обновления значений weight_per_meter в таблице stocks
на основе данных из таблицы products
"""
from flask import Flask
from models import db, Stock, Product
import sqlite3
import os

def update_stock_weights():
    """Обновляет значения weight_per_meter в таблице stocks"""
    # Создаем приложение Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metal_sales.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Инициализируем базу данных
    db.init_app(app)
    
    with app.app_context():
        # Получаем все товары на складе
        stocks = Stock.query.all()
        
        # Получаем все товары из прайс-листа
        products = Product.query.all()
        
        # Создаем словарь для быстрого поиска товаров по категории, названию и характеристикам
        product_dict = {}
        for product in products:
            key = f"{product.category}_{product.name}_{product.characteristics}"
            product_dict[key] = product.weight_per_meter
        
        # Обновляем значения weight_per_meter для товаров на складе
        updated_count = 0
        for stock in stocks:
            key = f"{stock.category}_{stock.name}_{stock.characteristics}"
            if key in product_dict:
                stock.weight_per_meter = product_dict[key]
                updated_count += 1
        
        # Сохраняем изменения
        db.session.commit()
        
        print(f"Обновлено {updated_count} записей в таблице stocks")

if __name__ == '__main__':
    update_stock_weights() 