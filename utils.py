import re
from datetime import datetime
from database import session, User


def validate_activation_code(code):
    """Проверка валидности кода активации"""
    # В реальном приложении коды должны храниться в базе данных
    # Здесь простой пример с чтением из файла
    try:
        with open('valid_codes.txt', 'r') as f:
            valid_codes = [line.strip() for line in f]
        return code.upper() in valid_codes
    except:
        return False


def validate_age(age_str):
    """Проверка возраста"""
    try:
        age = int(age_str)
        from config import MIN_AGE, MAX_AGE
        return MIN_AGE <= age <= MAX_AGE
    except:
        return False


def get_user_by_telegram_id(telegram_id):
    """Получить пользователя по Telegram ID"""
    return session.query(User).filter_by(telegram_id=telegram_id).first()


def calculate_compatibility(user1, user2):
    """Рассчитать совместимость двух пользователей"""
    score = 0

    # Совпадение профилей
    if user1.profile == user2.profile:
        score += 30

    # Совпадение интересов
    common_interests = set(user1.interests or []) & set(user2.interests or [])
    score += len(common_interests) * 10

    # Близость возраста
    age_diff = abs(user1.age - user2.age)
    if age_diff == 0:
        score += 20
    elif age_diff == 1:
        score += 10

    # Одинаковый класс
    if user1.grade == user2.grade and user1.class_letter == user2.class_letter:
        score += 15

    return min(score, 100)


def format_profile(user):
    """Форматирование анкеты пользователя для отображения"""
    profile_text = f"""
👤 *{user.full_name}*

📊 *Основная информация:*
• Возраст: {user.age} лет
• Пол: {'Мужской' if user.gender == 'male' else 'Женский'}
• Класс: {user.grade}{user.class_letter}
• Профиль: {user.profile.capitalize() if user.profile else 'Не указан'}

🎯 *Интересы:*
{', '.join(user.interests) if user.interests else 'Не указаны'}

📝 *О себе:*
{user.about if user.about else 'Не указано'}
"""

    # Добавляем статистику если есть
    if hasattr(user, 'compatibility'):
        profile_text += f"\n Совместимость по интересам: {user.compatibility}%"

    return profile_text