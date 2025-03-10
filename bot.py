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

# Глобальный словарь для хранения вопросов пользователей
user_questions = {}

# Сценарий для ответов на вопросы
FAQ = {
    "адрес": "Адрес школы: ул. Антонова, д. 14Б",
    "директор": "Директор школы: Выборнов Евгений Владимирович",
    "расписание": "Расписание можно найти по команде /schedule",
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

    # Добавляем кнопку "Комментарии" только для администратора
    if update.message and update.message.chat_id == ADMIN_CHAT_ID:
        keyboard.append([InlineKeyboardButton("📝 Показать комментарии", callback_data='show_comments')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с клавиатурой
    if update.callback_query:
        await update.callback_query.edit_message_text("Добро пожаловать в наш бот! Здесь вы можете найти информацию о школе, задать вопросы и оставить комментарии.", reply_markup=reply_markup)
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
            comments = file.readlines()[-10:]  # Последние 10 комментариев
            if comments:
                comments_text = "Последние комментарии:\n\n" + "".join(comments)
                await update.callback_query.edit_message_text(comments_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))
            else:
                await update.callback_query.edit_message_text("Комментариев пока нет.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))
    except FileNotFoundError:
        await update.callback_query.edit_message_text("Файл comments.txt не найден.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))
        log_error("Файл comments.txt не найден.")

# Обработчик нажатий на кнопки
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'location':
        # Отправка геопозиции школы
        await context.bot.send_location(chat_id=query.message.chat_id, latitude=LATITUDE, longitude=LONGITUDE)
        # Добавляем кнопку "Главное меню" после отправки локации
        await query.message.reply_text("Вы можете вернуться в главное меню:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))

    elif query.data == 'people_info':
        # Чтение данных из файла
        try:
            with open('people_info.txt', 'r', encoding='utf-8') as file:
                people_info = file.read()
            if people_info.strip():  # Проверка, что файл не пустой
                await query.edit_message_text(people_info, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))
            else:
                await query.edit_message_text("Файл people_info.txt пуст.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))
        except FileNotFoundError as e:
            await query.edit_message_text("Файл people_info.txt не найден.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))
            log_error(f"Файл people_info.txt не найден: {e}")

    elif query.data == 'faq':
        await query.edit_message_text("Задайте ваш вопрос. Бот постарается ответить.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))

    elif query.data == 'school_info':
        # Чтение информации о школе из файла
        try:
            with open('school_info.txt', 'r', encoding='utf-8') as file:
                school_info = file.read()
            if school_info.strip():  # Проверка, что файл не пустой
                await query.edit_message_text(school_info, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))
            else:
                await query.edit_message_text("Файл school_info.txt пуст.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))
        except FileNotFoundError as e:
            await query.edit_message_text("Файл school_info.txt не найден.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))
            log_error(f"Файл school_info.txt не найден: {e}")

    elif query.data == 'comments':
        # Сбор комментариев
        await query.edit_message_text("Напишите ваш комментарий или пожелание:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]]))
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

    elif query.data.startswith('reply_'):
        # Обработка кнопки "Ответить"
        user_id = int(query.data.split('_')[1])  # Получаем ID пользователя
        context.user_data['replying_to'] = user_id  # Сохраняем ID пользователя для ответа
        await query.edit_message_text(f"Вы отвечаете пользователю {user_id}. Напишите ответ:")

# Обработчик текстовых сообщений
async def message_handler(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id == ADMIN_CHAT_ID:
        # Если сообщение от администратора
        if 'replying_to' in context.user_data:
            # Если администратор отвечает на вопрос
            user_id = context.user_data['replying_to']
            response = update.message.text
            try:
                await context.bot.send_message(chat_id=user_id, text=f"Ответ от администратора: {response}")
                await update.message.reply_text("Ответ отправлен.")
                del context.user_data['replying_to']  # Удаляем состояние
            except Exception as e:
                await update.message.reply_text("Произошла ошибка при отправке ответа.")
                log_error(f"Ошибка при отправке ответа: {e}")
        else:
            # Если администратор просто пишет сообщение (не ответ)
            await update.message.reply_text("Вы можете ответить на вопрос, нажав кнопку 'Ответить'.")
    else:
        # Если сообщение от пользователя
        if context.user_data.get('awaiting_comment'):
            # Сохранение комментария
            comment = update.message.text
            try:
                with open('comments.txt', 'a', encoding='utf-8') as file:
                    file.write(f"{update.message.from_user.username}: {comment}\n")
                await update.message.reply_text("Спасибо за ваш комментарий!")
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
                keyboard = [[InlineKeyboardButton("Ответить", callback_data=f'reply_{update.message.from_user.id}')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_CHAT_ID,
                        text=f"Вопрос от пользователя {update.message.from_user.username}: {update.message.text}",
                        reply_markup=reply_markup
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
    application.add_handler(CommandHandler("schedule", send_schedule))  # Команда /schedule
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
