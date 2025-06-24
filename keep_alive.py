
from flask import Flask
from threading import Thread
import time
import socket

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>Telegram AI Bot</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>🤖 Telegram AI Bot активен!</h1>
        <p>Бот работает и готов к использованию.</p>
        <p>Время: <span id="time"></span></p>
        <script>
            function updateTime() {
                document.getElementById('time').innerHTML = new Date().toLocaleString();
            }
            updateTime();
            setInterval(updateTime, 1000);
        </script>
    </body>
    </html>
    """

@app.route('/status')
def status():
    return {
        "status": "active",
        "timestamp": time.time(),
        "message": "Bot is running"
    }

@app.route('/health')
def health():
    return "OK"

def is_port_in_use(port):
    """Проверяет, занят ли порт"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run():
    try:
        if not is_port_in_use(5000):
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        else:
            print("⚠️ Порт 5000 уже используется - Flask сервер уже запущен")
    except Exception as e:
        print(f"❌ Ошибка Flask сервера: {e}")

def keep_alive():
    if not is_port_in_use(5000):
        t = Thread(target=run)
        t.daemon = True
        t.start()
        print("✅ Keep-alive сервер запущен на порту 5000")
    else:
        print("✅ Keep-alive сервер уже работает на порту 5000")
