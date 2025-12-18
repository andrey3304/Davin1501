from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from config import SCHOOL_PROFILES, CLASS_LETTERS, INTERESTS


def get_grade_keyboard():
    grades = [7, 8, 9, 10, 11]

    keyboard = []
    row = []
    for grade in grades:
        row.append(InlineKeyboardButton(str(grade), callback_data=f"grade_{grade}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def get_class_letter_keyboard():
    letters = ["А", "Б", "В", "Г", "Д", "Е", "И", "К", "Л", "М"]

    keyboard = []
    row = []
    for letter in letters:
        row.append(InlineKeyboardButton(letter, callback_data=f"letter_{letter}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def get_main_menu():
    keyboard = [
        ["Моя анкета", "Искать единомышленника"],
        ["Мэтчи", "Настройки поиска"],
        ["Статистика", "Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_gender_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Мужской", callback_data="gender_male"),
            InlineKeyboardButton("Женский", callback_data="gender_female")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_profile_keyboard():
    buttons = []
    for profile in SCHOOL_PROFILES:
        buttons.append([InlineKeyboardButton(profile.capitalize(),
                       callback_data=f"profile_{profile}")])
    buttons.append([InlineKeyboardButton("Пропустить", callback_data="profile_skip")])
    return InlineKeyboardMarkup(buttons)


def get_class_letter_keyboard():
    buttons = []
    row = []
    for i, letter in enumerate(CLASS_LETTERS):
        row.append(InlineKeyboardButton(letter, callback_data=f"letter_{letter}"))
        if (i + 1) % 3 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def get_interests_keyboard():
    buttons = []
    row = []
    for i, interest in enumerate(INTERESTS):
        row.append(InlineKeyboardButton(interest, callback_data=f"interest_{interest}"))
        if (i + 1) % 3 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Готово", callback_data="interests_done")])
    return InlineKeyboardMarkup(buttons)


def get_like_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("❤️ Лайк", callback_data=f"like_{user_id}"),
            InlineKeyboardButton("👎 Пропустить", callback_data=f"skip_{user_id}")
        ],
        [
            InlineKeyboardButton("🚫 Пожаловаться", callback_data=f"report_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_match_keyboard(match_id):
    keyboard = [
        [
            InlineKeyboardButton("Написать сообщение",
                               callback_data=f"message_{match_id}"),
            InlineKeyboardButton("👀 Посмотреть анкету",
                               callback_data=f"view_{match_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_search_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Пол для поиска", callback_data="set_gender"),
            InlineKeyboardButton("Возраст", callback_data="set_age")
        ],
        [
            InlineKeyboardButton("Профиль класса", callback_data="set_profile"),
            InlineKeyboardButton("Назад", callback_data="back_to_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
