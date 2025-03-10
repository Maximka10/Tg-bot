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

# Сценарий для ответов на вопросы
FAQ = {
    "адрес": "Адрес школы: ул. Антонова, д. 14Б",
    "директор": "Директор школы: Выборнов Евгений Владимирович",
    "расписание": "Расписание можно найти по кнопке '📅 Расписание'.",
}

# Глобальная переменная для хранения вопросов
user_questions = {}

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
        [InlineKeyboardButton("💬 Комментарии и пожелания", callback_data='comments')],
        [InlineKeyboardButton("📅 Расписание", callback_data='schedule')],  # Кнопка "Расписание"
    ]

    # Добавляем кнопку "Показать комментарии" только для администратора
    if update.effective_chat.id == ADMIN_CHAT_ID:
        keyboard.append([InlineKeyboardButton("📝 Показать комментарии", callback_data='show_comments')])

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

# Функция для отображения последних комментариев
async def show_comments(update: Update, context: CallbackContext) -> None:
    comments = read_file('comments.txt')
    await update.callback_query.message.reply_text(comments)

# Обработчик нажатий на кнопки
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'location':
        # Отправка геопозиции школы
        await context.bot.send_location(chat_id=query.message.chat_id, latitude=LATITUDE, longitude=LONGITUDE)
        await show_main_menu(update, context)  # Возврат в главное меню

    elif query.data == 'people_info':
        # Чтение данных из файла
        people_info = read_file('people_info.txt')
        await query.message.reply_text(people_info)
        await show_main_menu(update, context)  # Возврат в главное меню

    elif query.data == 'faq':
        await query.message.reply_text("Задайте ваш вопрос. Бот постарается ответить.")

    elif query.data == 'school_info':
        # Чтение информации о школе из файла
        school_info = read_file('school_info.txt')
        await query.message.reply_text(school_info)
        await show_main_menu(update, context)  # Возврат в главное меню

    elif query.data == 'comments':
        # Сбор комментариев
        await query.message.reply_text("Напишите ваш комментарий или пожелание:")
        context.user_data['awaiting_comment'] = True

    elif query.data == 'show_comments':
        # Показ последних комментариев для администратора
        await show_comments(update, context)

    elif query.data == 'schedule':
        # Отправка расписания
        await send_schedule(update, context)

    elif query.data == 'main_menu':
        # Возврат в главное меню
        await show_main_menu(update, context)

# Обработчик текстовых сообщений
async def message_handler(update: Update, context: CallbackContext) -> None:
    logger.info(f"Получено сообщение: {update.message.text}")
    if context.user_data.get('awaiting_comment'):
        logger.info("Обработка комментария...")
        # Сохранение комментария
        comment = update.message.text
        try:
            with open('comments.txt', 'a', encoding='utf-8') as file:
                file.write(f"[{datetime.now()}] @{update.message.from_user.username}: {comment}\n")
            await update.message.reply_text("Спасибо за ваш комментарий!")
            # Пересылка комментария администратору
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"Новый комментарий от @{update.message.from_user.username}:\n{comment}"
            )
            logger.info("Комментарий сохранен и отправлен администратору.")
        except Exception as e:
            await update.message.reply_text("Произошла ошибка при сохранении комментария.")
            log_error(f"Ошибка при сохранении комментария: {e}")
        context.user_data['awaiting_comment'] = False
        await show_main_menu(update, context)  # Возврат в главное меню
    else:
        logger.info("Обработка вопроса...")
        # Ответы на вопросы
        question = update.message.text.lower()
        response = None

        # Поиск ответа в сценарии
        for keyword, answer in FAQ.items():
            if keyword in question:
                response = answer
                break

        if response:
            await update.message.reply_text(response)
            await show_main_menu(update, context)  # Возврат в главное меню
        else:
            logger.info("Вопрос не найден в FAQ. Пересылка администратору...")
            # Пересылка вопроса администратору
            user_questions[update.message.from_user.id] = update.message.text
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"Вопрос от пользователя {update.message.from_user.username}:\n{update.message.text}"
                )
                await update.message.reply_text("Извините, я не могу ответить на этот вопрос. Вопрос переадресован администратору.")
                logger.info("Вопрос успешно переслан администратору.")
            except Exception as e:
                await update.message.reply_text("Произошла ошибка при пересылке вопроса администратору.")
                log_error(f"Ошибка при пересылке вопроса администратору: {e}")
            await show_main_menu(update, context)  # Возврат в главное меню

# Обработка ошибок
async def error_handler(update: Update, context: CallbackContext) -> None:
    error_message = f"Update {update} caused error {context.error}"
    logger.warning(error_message)
    log_error(error_message)

# Основная функция
def main() -> None:
    # Создаем Application и передаем ему токен бота
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
