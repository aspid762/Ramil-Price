"""
Скрипт для добавления колонки weight_per_meter в таблицу stocks
"""
from flask import Flask
from models import db, Stock
import sqlite3
import os

def add_weight_per_meter_column():
    """Добавляет колонку weight_per_meter в таблицу stocks"""
    # Создаем приложение Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metal_sales.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Инициализируем базу данных
    db.init_app(app)
    
    # Получаем путь к файлу базы данных
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    # Проверяем, существует ли файл базы данных
    if not os.path.exists(db_path):
        print(f"База данных не найдена по пути: {db_path}")
        return
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем, существует ли колонка weight_per_meter
    cursor.execute("PRAGMA table_info(stocks)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'weight_per_meter' not in column_names:
        # Добавляем колонку weight_per_meter
        cursor.execute("ALTER TABLE stocks ADD COLUMN weight_per_meter FLOAT NOT NULL DEFAULT 0")
        conn.commit()
        print("Колонка weight_per_meter успешно добавлена в таблицу stocks")
    else:
        print("Колонка weight_per_meter уже существует в таблице stocks")
    
    # Закрываем соединение
    conn.close()

if __name__ == '__main__':
    add_weight_per_meter_column() 