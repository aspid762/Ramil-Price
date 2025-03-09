import sqlite3

# Подключаемся к базе данных
conn = sqlite3.connect('metal_sales.db')
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