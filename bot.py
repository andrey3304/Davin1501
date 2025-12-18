import logging

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

from config import MAX_PHOTOS
from database import UserState
from keyboards import *
from utils import *

TOKEN = "8366783262:AAFHbOSyuBT7gPDw5TkBvPKonwXYPi3__Qw"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SchoolDatingBot:
    def __init__(self):
        self.application = Application.builder().token(TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("reset", self.reset_profile))

        # Сообщения
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.handle_message
        ))

        # Фотографии
        self.application.add_handler(MessageHandler(
            filters.PHOTO, self.handle_photo
        ))

        # Callback queries
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

        # Ошибки
        self.application.add_error_handler(self.error_handler)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = get_user_by_telegram_id(update.effective_user.id)

        if not user:
            # Новый пользователь
            await update.message.reply_text(
                f"Добро пожаловать в систему внешкольного общения школы №{1501}!\n\n"
                "Для доступа к боту введите ваш уникальный код активации:"
            )
            self.set_user_state(update.effective_user.id, "awaiting_code")
        elif not user.is_active:
            await update.message.reply_text("Введите ваш код активации:")
            self.set_user_state(update.effective_user.id, "awaiting_code")
        elif not user.full_name:
            await update.message.reply_text(
                "Давайте создадим вашу анкету\n"
                "Введите ваше ФИО (например: Иванов Иван Иванович):"
            )
            self.set_user_state(update.effective_user.id, "awaiting_fullname")
        else:
            await update.message.reply_text(
                "Добро пожаловать назад!",
                reply_markup=get_main_menu()
            )
            self.set_user_state(update.effective_user.id, "main_menu")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        state = self.get_user_state(user_id)

        if state == "awaiting_code":
            await self.handle_activation_code(update, text)
        elif state == "awaiting_fullname":
            await self.handle_fullname(update, text)
        elif state == "awaiting_age":
            await self.handle_age(update, text)
        elif state == "awaiting_about":
            await self.handle_about(update, text)
        elif state == "awaiting_photos":
            await update.message.reply_text(
                "Загрузите фотографии или нажмите /skip чтобы пропустить"
            )
        elif state == "main_menu":
            await self.handle_main_menu(update, text)

    async def handle_activation_code(self, update: Update, code: str):
        """Проверка кода активации"""
        if validate_activation_code(code):
            user = get_user_by_telegram_id(update.effective_user.id)
            if not user:
                user = User(
                    telegram_id=update.effective_user.id,
                    activation_code=code.upper(),
                    is_active=True
                )
                session.add(user)
            else:
                user.is_active = True
                user.activation_code = code.upper()

            session.commit()

            await update.message.reply_text(
                "Код активирован успешно!\n\n"
                "Давайте создадим вашу анкету.\n"
                "Введите ваше ФИО (например: Иванов Иван Иванович):"
            )
            self.set_user_state(update.effective_user.id, "awaiting_fullname")
        else:
            await update.message.reply_text(
                "Неверный код активации. Попробуйте еще раз или "
                "обратитесь к администратору школы."
            )

    async def handle_fullname(self, update: Update, fullname: str):
        """Обработка ФИО"""
        if len(fullname.split()) < 2:
            await update.message.reply_text(
                "Пожалуйста, введите полное ФИО (Иванов Иван Иванович):"
            )
            return

        user = get_user_by_telegram_id(update.effective_user.id)
        user.full_name = fullname

        await update.message.reply_text(
            "Сколько вам лет? (от 12 до 18)"
        )
        self.set_user_state(update.effective_user.id, "awaiting_age")
        session.commit()

    async def handle_age(self, update: Update, age_text: str):
        """Обработка возраста"""
        if not validate_age(age_text):
            await update.message.reply_text(
                "Пожалуйста, введите корректный возраст от 12 до 18 лет:"
            )
            return

        user = get_user_by_telegram_id(update.effective_user.id)
        user.age = int(age_text)

        await update.message.reply_text(
            "Выберите ваш пол:",
            reply_markup=get_gender_keyboard()
        )
        session.commit()

    async def handle_about(self, update: Update, about_text: str):
        """Обработка информации о себе"""
        user = get_user_by_telegram_id(update.effective_user.id)
        user.about = about_text

        await update.message.reply_text(
            "Расскажите немного о себе (ваши увлечения, хобби и т.д.):\n"
            "(или напишите /skip чтобы пропустить)"
        )
        session.commit()

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка фотографий"""
        user = get_user_by_telegram_id(update.effective_user.id)
        state = self.get_user_state(user.telegram_id)

        if state == "awaiting_photos":
            if not user.photos:
                user.photos = []

            if len(user.photos) < MAX_PHOTOS:
                photo_id = update.message.photo[-1].file_id
                user.photos.append(photo_id)
                session.commit()

                remaining = MAX_PHOTOS - len(user.photos)
                if remaining > 0:
                    await update.message.reply_text(
                        f"Фото добавлено. Можно добавить еще {remaining} фото.\n"
                        "Отправьте еще фото или нажмите /done чтобы закончить."
                    )
                else:
                    await update.message.reply_text(
                        "Максимальное количество фото достигнуто.\n"
                        "Анкета создана!",
                        reply_markup=get_main_menu()
                    )
                    self.set_user_state(user.telegram_id, "main_menu")
            else:
                await update.message.reply_text(
                    "Достигнуто максимальное количество фото (5)."
                )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback запросов"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = update.effective_user.id
        user = get_user_by_telegram_id(user_id)

        if data.startswith("gender_"):
            gender = data.split("_")[1]
            user.gender = gender
            session.commit()

            # Вместо текстового ввода - показываем кнопки с классами
            await query.edit_message_text(
                "В каком вы классе?",
                reply_markup=get_grade_keyboard()
            )
            # Убираем состояние awaiting_grade, так как используем кнопки

        elif data.startswith("grade_"):  # Добавляем обработку выбора класса
            grade = data.split("_")[1]
            user.grade = int(grade)
            session.commit()

            await query.edit_message_text(
                "Выберите букву вашего класса:",
                reply_markup=get_class_letter_keyboard()
            )

        elif data.startswith("letter_"):
            class_letter = data.split("_")[1]
            user.class_letter = class_letter
            session.commit()

            await query.edit_message_text(
                "Выберите ваши интересы (можно несколько):",
                reply_markup=get_interests_keyboard()
            )
            self.set_temp_data(user_id, {"selected_interests": []})

        elif data.startswith("interest_"):
            interest = data.split("_")[1]
            temp_data = self.get_temp_data(user_id)

            if interest in temp_data["selected_interests"]:
                temp_data["selected_interests"].remove(interest)
            else:
                temp_data["selected_interests"].append(interest)

            self.set_temp_data(user_id, temp_data)

            selected = len(temp_data["selected_interests"])
            await query.edit_message_text(
                f"Выбрано интересов: {selected}\n"
                "Продолжайте выбирать или нажмите 'Готово':",
                reply_markup=get_interests_keyboard()
            )

        elif data == "interests_done":
            temp_data = self.get_temp_data(user_id)
            user.interests = temp_data["selected_interests"]
            session.commit()

            await query.edit_message_text(
                "Отлично! Теперь добавьте до 5 фотографий в вашу анкету.\n"
                "Отправьте фото или нажмите /skip чтобы пропустить:"
            )
            self.set_user_state(user_id, "awaiting_photos")

        elif data.startswith("like_"):
            liked_user_id = int(data.split("_")[1])
            await self.handle_like(user, liked_user_id, query)

        elif data.startswith("skip_"):
            # Пропуск анкеты
            await query.edit_message_text("Анкета пропущена")
            await self.show_next_profile(user, context)

        elif data.startswith("message_"):
            match_id = int(data.split("_")[1])
            match_user = get_user_by_telegram_id(match_id)

            await query.message.reply_text(
                f"Вы можете написать пользователю @{match_user.telegram_id}\n\n"
                f"Имя: {match_user.full_name}\n"
                f"Для конфиденциального обмена контактами."
            )

    async def handle_like(self, user, liked_user_id, query):
        """Обработка лайка"""
        liked_user = session.query(User).filter_by(telegram_id=liked_user_id).first()

        if not liked_user:
            await query.edit_message_text("Пользователь не найден")
            return

        # Добавляем лайк
        if not user.liked_users:
            user.liked_users = []

        if liked_user_id not in user.liked_users:
            user.liked_users.append(liked_user_id)

        # Проверяем взаимность
        match = False
        if liked_user.liked_users and user.telegram_id in liked_user.liked_users:
            match = True
            if not user.matches:
                user.matches = []
            if not liked_user.matches:
                liked_user.matches = []

            if liked_user_id not in user.matches:
                user.matches.append(liked_user_id)
            if user.telegram_id not in liked_user.matches:
                liked_user.matches.append(user.telegram_id)

            # Уведомляем другого пользователя
            await query.message.reply_text(
                f"У вас взаимный лайк с {liked_user.full_name}!\n"
                "Теперь вы можете написать друг другу"
            )

        session.commit()

        if not match:
            await query.edit_message_text("❤️ Вы поставили лайк!")

        # Показываем следующую анкету
        await self.show_next_profile(user, query.message.chat_id)

    async def show_next_profile(self, user, chat_id):
        """Показать следующую анкету для оценки"""
        # Получаем всех пользователей, которых еще не видели
        all_users = session.query(User).filter(
            User.telegram_id != user.telegram_id,
            User.is_active == True,
            User.full_name != None
        ).all()

        # Фильтруем по настройкам поиска
        filtered_users = []
        for other_user in all_users:
            # Проверка возраста
            if not (user.min_age <= other_user.age <= user.max_age):
                continue

            # Проверка пола
            if user.search_gender != "any" and other_user.gender != user.search_gender:
                continue

            # Проверка профиля
            if user.search_profile != "any" and other_user.profile != user.search_profile:
                continue

            # Проверка, что еще не ставили лайк/дизлайк
            if other_user.telegram_id in (user.liked_users or []):
                continue

            filtered_users.append(other_user)

        if not filtered_users:
            await self.application.bot.send_message(
                chat_id,
                "Вы просмотрели всех зарегестрированных учеников. Загляните позже!"
            )
            return

        # Показываем следующего пользователя
        next_user = filtered_users[0]
        next_user.compatibility = calculate_compatibility(user, next_user)

        # Формируем сообщение с анкетой
        message = format_profile(next_user)

        # Отправляем фото если есть
        if next_user.photos:
            await self.application.bot.send_photo(
                chat_id,
                photo=next_user.photos[0],
                caption=message,
                parse_mode="Markdown",
                reply_markup=get_like_keyboard(next_user.telegram_id)
            )
        else:
            await self.application.bot.send_message(
                chat_id,
                message,
                parse_mode="Markdown",
                reply_markup=get_like_keyboard(next_user.telegram_id)
            )

    async def handle_main_menu(self, update: Update, text: str):
        """Обработка главного меню"""
        if text == "Моя анкета":
            await self.show_my_profile(update)
        elif text == "Смотреть анкеты":
            await self.start_browsing(update)
        elif text == "Мэтчи":
            await self.show_matches(update)
        elif text == "Настройки поиска":
            await self.show_search_settings(update)
        elif text == "Статистика":
            await self.show_stats(update)
        elif text == "Помощь":
            await self.help_command(update, None)

    async def show_my_profile(self, update: Update):
        """Показать свою анкету"""
        user = get_user_by_telegram_id(update.effective_user.id)

        if not user.full_name:
            await update.message.reply_text("Анкета еще не создана!")
            return

        message = format_profile(user)

        if user.photos:
            await update.message.reply_photo(
                photo=user.photos[0],
                caption=message,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode="Markdown"
            )

    async def start_browsing(self, update: Update):
        """Начать просмотр анкет"""
        user = get_user_by_telegram_id(update.effective_user.id)
        await self.show_next_profile(user, update.effective_chat.id)

    async def show_matches(self, update: Update):
        """Показать мэтчи"""
        user = get_user_by_telegram_id(update.effective_user.id)

        if not user.matches:
            await update.message.reply_text("У вас еще нет взаимных симпатий 😔")
            return

        message = "Мэтчи:\n\n"
        for i, match_id in enumerate(user.matches[:10], 1):
            match_user = get_user_by_telegram_id(match_id)
            if match_user:
                message += f"{i}. {match_user.full_name} - {match_user.grade}{match_user.class_letter}\n"

        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Посмотреть все мэтчи", callback_data="view_all_matches")
            ]])
        )

    async def show_search_settings(self, update: Update):
        """Показать настройки поиска"""
        user = get_user_by_telegram_id(update.effective_user.id)

        message = (
            "⚙️ *Настройки поиска*\n\n"
            f"• Пол: {user.search_gender}\n"
            f"• Возраст: от {user.min_age} до {user.max_age}\n"
            f"• Профиль: {user.search_profile if user.search_profile != 'any' else 'любой'}"
        )

        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=get_search_settings_keyboard()
        )

    async def show_stats(self, update: Update):
        """Показать статистику"""
        user = get_user_by_telegram_id(update.effective_user.id)

        total_users = session.query(User).filter_by(is_active=True).count()
        total_matches = len(user.matches) if user.matches else 0
        total_likes = len(user.liked_users) if user.liked_users else 0

        message = (
            f" *Ваша статистика*\n\n"
            f"• Всего пользователей: {total_users}\n"
            f"• Ваши лайки: {total_likes}\n"
            f"• Взаимные лайки: {total_matches}\n"
            f"• Просмотрено анкет: {total_likes + (session.query(User).count() - total_users - 1)}"
        )

        await update.message.reply_text(message, parse_mode="Markdown")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать справку"""
        help_text = (
            "📚 *Помощь по боту*\n\n"
            "• /start - Начать работу с ботом\n"
            "• /help - Показать эту справку\n"
            "• /reset - Сбросить анкету\n\n"
            "📝 *Как это работает:*\n"
            "1. Создайте анкету\n"
            "2. Смотрите анкеты других учеников\n"
            "3. Ставьте лайки понравившимся\n"
            "4. При взаимной симпатии получаете контакт\n\n"
            "⚠️ *Правила:*\n"
            "- Уважайте других пользователей\n"
            "- Не спамьте\n"
            "- Используйте реальные данные\n"
            "- При нарушении правил - бан\n\n"
            "По вопросам: обратитесь к администратору школы"
        )

        if update.message:
            await update.message.reply_text(help_text, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.reply_text(help_text, parse_mode="Markdown")

    async def reset_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сброс анкеты"""
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Да", callback_data="reset_confirm"),
            InlineKeyboardButton("Нет", callback_data="reset_cancel")
        ]])

        await update.message.reply_text(
            "⚠️ Вы уверены, что хотите сбросить анкету? Это действие нельзя отменить.",
            reply_markup=keyboard
        )

    # Вспомогательные методы для работы с состояниями
    def set_user_state(self, telegram_id, state):
        """Установить состояние пользователя"""
        user_state = session.query(UserState).filter_by(telegram_id=telegram_id).first()
        if not user_state:
            user_state = UserState(telegram_id=telegram_id, state=state)
            session.add(user_state)
        else:
            user_state.state = state
        session.commit()

    def get_user_state(self, telegram_id):
        """Получить состояние пользователя"""
        user_state = session.query(UserState).filter_by(telegram_id=telegram_id).first()
        return user_state.state if user_state else "start"

    def set_temp_data(self, telegram_id, data):
        """Сохранить временные данные"""
        user_state = session.query(UserState).filter_by(telegram_id=telegram_id).first()
        if not user_state:
            user_state = UserState(telegram_id=telegram_id, temp_data=data)
            session.add(user_state)
        else:
            user_state.temp_data = data
        session.commit()

    def get_temp_data(self, telegram_id):
        """Получить временные данные"""
        user_state = session.query(UserState).filter_by(telegram_id=telegram_id).first()
        return user_state.temp_data if user_state and user_state.temp_data else {}

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Exception while handling an update: {context.error}")

        try:
            await context.bot.send_message(
                update.effective_user.id,
                "Произошла ошибка. Пожалуйста, попробуйте позже."
            )
        except:
            pass

    def run(self):
        """Запуск бота"""
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = SchoolDatingBot()
    print("Бот запущен...")
    bot.run()