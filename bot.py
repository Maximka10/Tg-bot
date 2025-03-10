async def message_handler(update: Update, context: CallbackContext) -> None:
    logger.info(f"Получено сообщение: {update.message.text}")
    
    if context.user_data.get('awaiting_comment'):
        logger.info("Обработка комментария...")
        # Сохранение комментария
        comment = update.message.text
        try:
            with open('comments.txt', 'a', encoding='utf-8') as file:
                file.write(f"[{datetime.now()}] @{update.message.from_user.username}: {comment}\n")
            logger.info("Комментарий успешно записан в файл.")
            await update.message.reply_text("Спасибо за ваш комментарий!")
            
            # Пересылка комментария администратору
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"Новый комментарий от @{update.message.from_user.username}:\n{comment}"
                )
                logger.info(f"Комментарий отправлен администратору: {ADMIN_CHAT_ID}")
            except Exception as e:
                logger.error(f"Ошибка при отправке комментария администратору: {e}")
                await update.message.reply_text("Произошла ошибка при отправке комментария администратору.")
        except Exception as e:
            logger.error(f"Ошибка при записи комментария: {e}")
            await update.message.reply_text("Произошла ошибка при сохранении комментария.")
        finally:
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
                logger.info(f"Вопрос отправлен администратору: {ADMIN_CHAT_ID}")
            except Exception as e:
                logger.error(f"Ошибка при отправке вопроса администратору: {e}")
                await update.message.reply_text("Произошла ошибка при пересылке вопроса администратору.")
            await show_main_menu(update, context)  # Возврат в главное меню
