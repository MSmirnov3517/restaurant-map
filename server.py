from flask import Flask, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import logging
import json
import sys
import os

app = Flask(__name__)
CORS(app)
#Строка для теста. часть вторая
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log.txt', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Конфигурация из файла
try:
    with open('config.json', encoding='utf-8') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    logging.error("Файл config.json не найден")
    config = {"file_path": "restaurants.xlsx"}

def safe_date_conversion(df, col):
    """
    Безопасное преобразование столбца с датами в формат ISO.
    """
    try:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        df[col] = df[col].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else None)
        logging.info(f"Столбец '{col}' успешно преобразован в формат ISO.")
    except Exception as e:
        logging.error(f"Ошибка при преобразовании столбца '{col}': {e}")

def read_excel_data(file_path):
    """
    Читает данные из Excel-файла.
    """
    try:
        df = pd.read_excel(file_path, engine='openpyxl')

        for col in df.columns:
            if 'Дата аудита' in col:
                safe_date_conversion(df, col)

        # Корректная замена NaN на None
        df = df.where(pd.notnull(df), None)

        logging.info("Данные успешно прочитаны из файла %s", file_path)
        return df
    except FileNotFoundError:
        logging.error("Файл %s не найден", file_path)
        return None
    except Exception as e:
        logging.error("Ошибка при чтении файла: %s", e)
        return None

@app.route('/api/restaurants')
def get_restaurants():
    """
    Возвращает данные из restaurants.xlsx в формате JSON.
    """
    try:
        file_path = config.get('file_path', 'restaurants.xlsx')
        df = read_excel_data(file_path)
        if df is None:
            return jsonify({'error': f'Не удалось прочитать файл {file_path}'}), 500

        logging.info("Первые 5 строк DataFrame перед преобразованием в JSON:\n%s", df.head().to_string())

        data = df.to_dict(orient='records')
        logging.info("Отправлено %d записей", len(data))
        return jsonify(data)
    except Exception as e:
        logging.error("Ошибка в /api/restaurants: %s", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/')
def serve_index():
    """
    Отдает index.html для корневого пути.
    """
    try:
        return send_file('index.html')
    except FileNotFoundError:
        logging.error("Файл index.html не найден")
        return jsonify({"error": "Файл index.html не найден"}), 404

@app.route('/favicon.ico')
def favicon():
    """
    Отдает favicon.ico или пустой ответ, если файл отсутствует.
    """
    if os.path.exists('favicon.ico'):
        return send_file('favicon.ico')
    return '', 204

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
