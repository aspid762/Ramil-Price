"""
Скрипт для обновления значений weight_per_meter в таблице stocks
на основе данных из таблицы products
"""
import sqlite3
import os

def update_stock_weights():
    """Обновляет значения weight_per_meter в таблице stocks"""
    # Подключаемся к базе данных
    conn = sqlite3.connect('metal_sales.db')
    cursor = conn.cursor()
    
    # Получаем все товары из прайс-листа
    cursor.execute("SELECT category, name, characteristics, weight_per_meter FROM products")
    products = cursor.fetchall()
    
    # Создаем словарь для быстрого поиска товаров по категории, названию и характеристикам
    product_dict = {}
    for product in products:
        category, name, characteristics, weight = product
        key = f"{category}_{name}_{characteristics}"
        product_dict[key] = weight
    
    # Получаем все товары на складе
    cursor.execute("SELECT id, category, name, characteristics FROM stocks")
    stocks = cursor.fetchall()
    
    # Обновляем значения weight_per_meter для товаров на складе
    updated_count = 0
    for stock in stocks:
        stock_id, category, name, characteristics = stock
        key = f"{category}_{name}_{characteristics}"
        if key in product_dict:
            weight = product_dict[key]
            cursor.execute("UPDATE stocks SET weight_per_meter = ? WHERE id = ?", (weight, stock_id))
            updated_count += 1
    
    # Сохраняем изменения
    conn.commit()
    
    # Закрываем соединение
    conn.close()
    
    print(f"Обновлено {updated_count} записей в таблице stocks")

if __name__ == '__main__':
    update_stock_weights() 