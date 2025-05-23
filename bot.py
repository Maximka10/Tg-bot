import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters
from datetime import datetime

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваши данные
LATITUDE = 53.188071  # Широта
LONGITUDE = 45.065603  # Долгота
ADMIN_CHAT_ID = 704381821  # ID администратора
TOKEN = "8132367709:AAFiFNFSLBG39Z-4Xj3LBPiJxkjZjKAy5Z4"  # Токен бота

# Глобальные переменные
user_questions = {}  # Словарь для хранения вопросов пользователей: {message_id: user_id}

# Функция для записи ошибок в файл
def log_error(error_message: str) -> None:
    with open('errors.txt', 'a', encoding='utf-8') as file:
        file.write(f"[{datetime.now()}] {error_message}\n")

# Функция для чтения файла
def read_file(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:
                raise ValueError(f"Файл {filename} пуст.")
            return content
    except FileNotFoundError:
        log_error(f"Файл {filename} не найден.")
        return f"Файл {filename} не найден."
    except Exception as e:
        log_error(f"Ошибка при чтении файла {filename}: {e}")
        return f"Ошибка при чтении файла {filename}."

# Функция для отображения главного меню
async def show_main_menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("📍 Местоположение школы", callback_data='location')],
        [InlineKeyboardButton("📄 Информация о людях", callback_data='people_info')],
        [InlineKeyboardButton("❓ Вопрос-ответ", callback_data='faq')],
        [InlineKeyboardButton("🏫 Информация о школе", callback_data='school_info')],
        [InlineKeyboardButton("📅 Расписание", callback_data='schedule')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с клавиатурой
    if update.callback_query:
        await update.callback_query.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Функция для отправки расписания
async def send_schedule(update: Update, context: CallbackContext) -> None:
    try:
        # Отправляем изображение с расписанием
        with open('gr.jpeg', 'rb') as photo:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)
        await show_main_menu(update, context)  # Возврат в главное меню
    except FileNotFoundError:
        await update.message.reply_text("Файл с расписанием не найден.")
        log_error("Файл gr.jpeg не найден.")
    except Exception as e:
        await update.message.reply_text("Произошла ошибка при отправке расписания.")
        log_error(f"Ошибка при отправке расписания: {e}")

# Функция для старта бота
async def start(update: Update, context: CallbackContext) -> None:
    # Чтение приветственного сообщения из файла
    welcome_message = read_file('welcome.txt')

    # Отправляем приветственное сообщение и показываем меню
    await update.message.reply_text(welcome_message)
    await show_main_menu(update, context)

# Функция для отображения информации о людях
async def show_people_info(update: Update, context: CallbackContext) -> None:
    people_info = read_file('people_info.txt')
    await update.callback_query.message.reply_text(people_info)
    await show_main_menu(update, context)  # Возврат в главное меню

# Функция для отображения информации о школе
async def show_school_info(update: Update, context: CallbackContext) -> None:
    school_info = read_file('school_info.txt')
    await update.callback_query.message.reply_text(school_info)
    await show_main_menu(update, context)  # Возврат в главное меню

# Обработчик нажатий на кнопки
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'location':
        # Отправка геопозиции школы
        await context.bot.send_location(chat_id=query.message.chat_id, latitude=LATITUDE, longitude=LONGITUDE)
        await show_main_menu(update, context)  # Возврат в главное меню

    elif query.data == 'people_info':
        # Показ информации о людях
        await show_people_info(update, context)

    elif query.data == 'faq':
        await query.message.reply_text("Задайте ваш вопрос. Бот постарается ответить.")

    elif query.data == 'school_info':
        # Показ информации о школе
        await show_school_info(update, context)

    elif query.data == 'schedule':
        # Отправка расписания
        await send_schedule(update, context)

    elif query.data == 'main_menu':
        # Возврат в главное меню
        await show_main_menu(update, context)

# Обработчик текстовых сообщений
async def message_handler(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id == ADMIN_CHAT_ID:
        # Если сообщение от администратора
        if update.message.reply_to_message:
            # Если администратор отвечает на сообщение
            replied_message_id = update.message.reply_to_message.message_id
            if replied_message_id in user_questions:
                # Получаем ID пользователя, который задал вопрос
                user_id = user_questions[replied_message_id]
                # Отправляем ответ пользователю
                await context.bot.send_message(chat_id=user_id, text=f"Ответ от администратора:\n{update.message.text}")
                await update.message.reply_text(f"Ответ отправлен пользователю с ID: {user_id}.")
                # Удаляем запись о вопросе
                del user_questions[replied_message_id]
            else:
                await update.message.reply_text("Ошибка: не найден ID пользователя для этого вопроса.")
                logger.error(f"Не найден ID пользователя для сообщения с ID: {replied_message_id}")
        else:
            await update.message.reply_text("Ответьте на сообщение с вопросом, чтобы отправить ответ пользователю.")
        return

    # Ответы на вопросы
    question = update.message.text
    user_id = update.message.from_user.id

    # Пересылка вопроса администратору
    sent_message = await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"Вопрос от пользователя @{update.message.from_user.username} (ID: {user_id}):\n{question}"
    )
    await update.message.reply_text("Ваш вопрос переадресован администратору. Ожидайте ответа.")

    # Сохраняем ID сообщения и ID пользователя
    user_questions[sent_message.message_id] = user_id
    logger.info(f"Сохранен вопрос от пользователя {user_id} с ID сообщения: {sent_message.message_id}")

# Основная функция
def main() -> None:
    # Создаем Application и передаем ему токен бота
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Запуск бота с игнорированием старых обновлений
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
