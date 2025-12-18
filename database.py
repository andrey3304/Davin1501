from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    activation_code = Column(String(50))
    is_active = Column(Boolean, default=False)

    # Анкетные данные
    full_name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(10))  # "male" или "female"
    grade = Column(Integer)  # Класс
    class_letter = Column(String(5))  # Буква класса
    profile = Column(String(20))  # Профиль класса
    interests = Column(JSON)  # Список интересов
    about = Column(Text, nullable=True)

    # Фотографии (храним file_id)
    photos = Column(JSON, default=[])

    # Лайки и мэтчи
    liked_users = Column(JSON, default=[])  # Кому поставил лайк
    matches = Column(JSON, default=[])  # Взаимные лайки

    # Настройки поиска
    search_gender = Column(String(10), default="any")  # any, male, female
    min_age = Column(Integer, default=14)
    max_age = Column(Integer, default=18)
    search_profile = Column(String(20), default="any")  # any или конкретный профиль


class UserState(Base):
    __tablename__ = 'user_states'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    state = Column(String(50), default="start")
    temp_data = Column(JSON, default={})


# Создаем базу данных
engine = create_engine('sqlite:///school_dating.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()