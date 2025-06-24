import logging
import requests
import asyncio
import nest_asyncio
import os
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from keep_alive import keep_alive

# Активация поддержки вложенных event loop'ов
nest_asyncio.apply()

# Ключи из переменных окружения
OPENROUTER_API_KEY = "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"
TELEGRAM_TOKEN = "8003773351:AAHimIBFtARHS_1chitfqYfP397dhtWV85s"

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Функция обращения к OpenRouter
def ask_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{
            "role": "user",
            "content": prompt
        }]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers,
                             json=data)
    if response.ok:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Ошибка OpenRouter: {response.status_code} — {response.text}"

# Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action("typing")
    reply = ask_openrouter(user_message)
    await update.message.reply_text(reply)

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "Привет, чем я могу вам помочь?"
    await update.message.reply_text(welcome_text)

# Основная логика запуска бота
async def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен!")
    await app.run_polling()

# Бесконечный цикл с автоперезапуском
def main_loop():
    keep_alive()
    while True:
        try:
            asyncio.run(run_bot())
        except Exception as e:
            print(f"❌ Бот упал с ошибкой: {e}")
            print("🔁 Перезапуск через 5 секунд...")
            time.sleep(5)

# Точка входа
if __name__ == "__main__":
    main_loop()
