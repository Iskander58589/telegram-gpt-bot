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
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Функция обращения к OpenRouter с fallback моделями
def ask_openrouter(prompt):
    try:
        if not OPENROUTER_API_KEY:
            return "⚠️ API ключ OpenRouter не найден в переменных окружения"
        
        # Список моделей для попытки (от бесплатных к платным)
        models_to_try = [
            "meta-llama/llama-3.2-3b-instruct:free",
            "google/gemma-2-9b-it:free", 
            "microsoft/phi-3-mini-128k-instruct:free",
            "huggingfaceh4/zephyr-7b-beta:free",
            "openchat/openchat-7b:free"
        ]
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://replit.com",
            "X-Title": "Telegram Bot"
        }
        
        # Пробуем модели по очереди
        for model in models_to_try:
            data = {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
                "max_tokens": 1000,
                "temperature": 0.7
            }
        
            response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                     headers=headers,
                                     json=data,
                                     timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    print(f"✅ Успешно использована модель: {model}")
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"⚠️ Пустой ответ от модели {model}, пробуем следующую...")
                    continue
            elif response.status_code == 404:
                print(f"❌ Модель {model} не найдена, пробуем следующую...")
                continue
            elif response.status_code == 401:
                return "🔑 Неверный API ключ OpenRouter"
            elif response.status_code == 402:
                return "💳 Недостаточно средств на балансе OpenRouter"
            elif response.status_code == 429:
                print(f"⏳ Лимит превышен для {model}, пробуем следующую...")
                continue
            else:
                error_text = response.text[:200] if response.text else "Неизвестная ошибка"
                print(f"❌ Ошибка {response.status_code} для модели {model}: {error_text}")
                continue
        
        # Если все модели не сработали
        return "❌ Не удалось получить ответ ни от одной модели. Попробуйте позже."
            
    except requests.exceptions.Timeout:
        return "⏰ Превышено время ожидания ответа от AI"
    except requests.exceptions.ConnectionError:
        return "🌐 Проблемы с подключением к AI сервису"
    except KeyError as e:
        return f"⚠️ Неверный формат ответа от API: {str(e)}"
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return f"⚠️ Неожиданная ошибка: {str(e)}"

# Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        await update.message.chat.send_action("typing")
        reply = ask_openrouter(user_message)
        await update.message.reply_text(reply)
    except Exception as e:
        print(f"❌ Ошибка в обработке сообщения: {e}")
        try:
            await update.message.reply_text("⚠️ Извините, произошла ошибка при обработке сообщения")
        except:
            pass

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "Привет, чем я могу вам помочь?"
    await update.message.reply_text(welcome_text)

# Основная логика запуска бота
async def run_bot():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN не найден в переменных окружения!")
        return
    
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY не найден в переменных окружения!")
        return
    
    print(f"🔑 Токены найдены:")
    print(f"   - Telegram: {'✅' if TELEGRAM_TOKEN else '❌'}")
    print(f"   - OpenRouter: {'✅' if OPENROUTER_API_KEY else '❌'}")
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен и готов к работе!")
    await app.run_polling()

# Бесконечный цикл с автоперезапуском
def main_loop():
    keep_alive()
    while True:
        try:
            print("🚀 Запуск бота...")
            asyncio.run(run_bot())
        except KeyboardInterrupt:
            print("⏹️ Бот остановлен пользователем")
            break
        except Exception as e:
            print(f"❌ Бот упал с ошибкой: {type(e).__name__}: {e}")
            print("🔁 Перезапуск через 5 секунд...")
            time.sleep(5)

# Точка входа
if __name__ == "__main__":
    main_loop()
