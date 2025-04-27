from flask import Flask, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import logging
import json
import sys
import os

app = Flask(__name__)
CORS(app)  # Включаем CORS для поддержки запросов с локального index.html

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log.txt', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    encoding='utf-8'
)

# Конфигурация из файла
try:
    with open('config.json') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    logging.error("Файл config.json не найден")
    config = {"file_path": "restaurants.xlsx"}

def read_excel_data(file_path):
    """
    Читает данные из Excel-файла.

    Args:
        file_path (str): Путь к файлу Excel.

    Returns:
        pandas.DataFrame: Данные из файла.
    """
    try:
        df = pd.read_excel(file_path)
        logging.info("Данные успешно прочитаны из файла %s", file_path)
        return df
    except FileNotFoundError:
        logging.error("Файл %s не найден", file_path)
        return None
    except Exception as e:
        logging.error("Ошибка при чтении файла: %s", e)
        return None

@app.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    """
    API-эндпоинт для получения данных ресторанов.

    Returns:
        JSON: Данные из Excel-файла.
    """
    file_path = config.get("file_path", "restaurants.xlsx")
    df = read_excel_data(file_path)
    if df is None:
        return jsonify({"error": "Не удалось загрузить данные"}), 500
    # Конвертация дат в ISO-формат для JSON
    date_columns = [col for col in df.columns if 'Дата аудита' in col]
    for col in date_columns:
        df[col] = df[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)
    # Заменяем NaN на null
    df = df.fillna(value=None)
    # Возвращаем JSON без экранирования Unicode
    return app.response_class(
        response=json.dumps(df.to_dict(orient='records'), ensure_ascii=False),
        mimetype='application/json'
    )

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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)