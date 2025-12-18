import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("8366783262:AAFHbOSyuBT7gPDw5TkBvPKonwXYPi3__Qw")
ADMIN_ID = int(os.getenv("5256572381", 0))

# Настройки школы
SCHOOL_NUMBER = "1501"
SCHOOL_PROFILES = ["Инженерный", "ИТ", "Математический"]
CLASS_LETTERS = ["А", "Б", "В", "Г", "Д"]
INTERESTS = [
    "Программирование", "Математика", "Физика", "Робототехника",
    "Дизайн", "Музыка", "Спорт", "Кино", "Книги", "Наука",
    "Искусство", "Путешествия", "Игры", "Кулинария"
]

# Ограничения
MAX_PHOTOS = 5
MIN_AGE = 12
MAX_AGE = 18
