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

# Функция для записи ошибок в файл
def log_error(error_message: str) -> None:
    with open('errors.txt', 'a', encoding='utf-8') as file:
        file.write(f"[{datetime.now()}] {error_message}\n")

# Функция для чтения приветственного сообщения из файла
def read_welcome_message() -> str:
    try:
        with open('welcome.txt', 'r', encoding='utf-8') as file:
            welcome_message = file.read().strip()  # Убираем лишние пробелы и переносы строк
            if not welcome_message:  # Если файл пустой
                raise ValueError("Файл welcome.txt пуст.")
            return welcome_message
    except FileNotFoundError:
        log_error("Файл welcome.txt не найден.")
        return "Добро пожаловать! Выберите действие:"
    except Exception as e:
        log_error(f"Ошибка при чтении welcome.txt: {e}")
        return "Добро пожаловать! Выберите действие:"

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
    welcome_message = read_welcome_message()

    # Отправляем приветственное сообщение и показываем меню
    await update.message.reply_text(welcome_message)
    await show_main_menu(update, context)

# Функция для отображения последних комментариев
async def show_comments(update: Update, context: CallbackContext) -> None:
    try:
        with open('comments.txt', 'r', encoding='utf-8') as file:
            comments = file.readlines()  # Читаем все комментарии
            if comments:
                # Отображаем последние 10 комментариев
                comments_text = "Последние комментарии:\n\n" + "".join(comments[-10:])
                await update.callback_query.message.reply_text(comments_text)
            else:
                await update.callback_query.message.reply_text("Комментариев пока нет.")
    except FileNotFoundError:
        await update.callback_query.message.reply_text("Файл comments.txt не найден.")
        log_error("Файл comments.txt не найден.")

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
        try:
            with open('people_info.txt', 'r', encoding='utf-8') as file:
                people_info = file.read()
            if people_info.strip():  # Проверка, что файл не пустой
                await query.message.reply_text(people_info)
            else:
                await query.message.reply_text("Файл people_info.txt пуст.")
        except FileNotFoundError as e:
            await query.message.reply_text("Файл people_info.txt не найден.")
            log_error(f"Файл people_info.txt не найден: {e}")

    elif query.data == 'faq':
        await query.message.reply_text("Задайте ваш вопрос. Бот постарается ответить.")

    elif query.data == 'school_info':
        # Чтение информации о школе из файла
        try:
            with open('school_info.txt', 'r', encoding='utf-8') as file:
                school_info = file.read()
            if school_info.strip():  # Проверка, что файл не пустой
                await query.message.reply_text(school_info)
            else:
                await query.message.reply_text("Файл school_info.txt пуст.")
        except FileNotFoundError as e:
            await query.message.reply_text("Файл school_info.txt не найден.")
            log_error(f"Файл school_info.txt не найден: {e}")

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
    if context.user_data.get('awaiting_comment'):
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
        except Exception as e:
            await update.message.reply_text("Произошла ошибка при сохранении комментария.")
            log_error(f"Ошибка при сохранении комментария: {e}")
        context.user_data['awaiting_comment'] = False
        await show_main_menu(update, context)  # Возврат в главное меню
    else:
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
            # Пересылка вопроса администратору
            user_questions[update.message.from_user.id] = update.message.text
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"Вопрос от пользователя {update.message.from_user.username}:\n{update.message.text}"
                )
                await update.message.reply_text("Извините, я не могу ответить на этот вопрос. Вопрос переадресован администратору.")
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
