import os
import random
import sys
from enum import Enum

import telebot
from dotenv import load_dotenv
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from db import (
    add_or_update_user,
    get_all_users,
    get_latest_events,
    get_user_count,
    init_db,
    log_event,
)

# Загружаем переменные из .env
load_dotenv()

# Получаем значение TOKEN
token = os.getenv("TOKEN") or ""
if not token:
    print("TOKEN not found in .env")
    sys.exit(0)

init_db()


class UsersStates(Enum):
    DEFAULT = 1
    FEEDBACKKING = 2


admin = int(os.getenv("ADMIN") or "0")
admins = [admin] if admin else []
users_states: dict[int, UsersStates] = {}

bot = telebot.TeleBot(token)


hearts = """Вы хотите сердечко сейчас?
    ❤️‍🩹,🩷,🖤,💜 - обычные сердечки;
    🩶,🤍,🤎 - необычные сердечки;
    💛,🧡,❤️ - редкие сердечки;
    🩵,💙 - очень редкие сердечки;
    💕,💞,💘 - эпические сердечки;
    💓,💗,💖 - мифические сердечки;
    💝,❣️ -  легендарные сердечки;
    ❤️‍🔥 - невозможно получимое сердечко."""


@bot.message_handler(commands=["start"])
def start(message):
    mainmenu = types.InlineKeyboardMarkup()
    key0 = types.InlineKeyboardButton(
        text="Запустить бота ДА/НЕТ от этого автора.(пока не работает)",
        url="https://t.me/DA_HET_bot",
    )
    mainmenu.add(key0)
    bot.send_message(
        message.from_user.id,
        """Здравствуйте!\n
Этот бот создан пользователем @KAPAC1D в 2026 году.\n
Он выбирает ваше cердечко сейчас. Для запуска нажмите Menu и выберите функцию. Также есть у нас ещё бот:""",
        reply_markup=mainmenu,
    )


@bot.message_handler(commands=["heart"])
def get_text_messages(message: Message):
    if message.from_user is not None:
        add_or_update_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
    mainmenu = types.InlineKeyboardMarkup()
    key1 = types.InlineKeyboardButton(text="Получить сердечко", callback_data="but1")
    key2 = types.InlineKeyboardButton(text="Шансы", callback_data="but2")
    mainmenu.add(key1, key2)
    if message.from_user is not None:
        bot.send_message(message.from_user.id, hearts, reply_markup=mainmenu)


@bot.callback_query_handler(func=lambda _: True)
def callback_inline(call):
    if call.data == "but1":
        result = random.choices(
            [
                "❤️‍🩹 - обычное сердечко",
                "🩷 - обычное сердечко",
                "🖤 - обычное сердечко",
                "💜 - обычное сердечко",
                "🩶 - необычное сердечко",
                "🤍 - необычное сердечко",
                "🤎 - необычное сердечко",
                "💛 - редкое сердечко",
                "🧡 - редкое сердечко",
                "❤️ - редкое сердечко",
                "🩵 - очень редкое сердечко ",
                "💙 - очень редкое сердечко",
                "💕 - эпическое сердечко",
                "💞 - эпическое сердечко",
                "💘 - эпическое сердечко",
                "💓 - мифическое сердечко",
                "💗 - мифическое сердечко",
                "💖 - мифическое сердечко",
                "💝 - ЛЕГЕНДАРНОЕ СЕРДЕЧКО!!! Делай скриншот и отпрвляй @KAPAC1D !",
                "❣️ - ЛЕГЕНДАРНОЕ СЕРДЕЧКО!!! Делай скриншот и отпрвляй @KAPAC1D !",
                "❤️‍🔥 - НЕВОЗМОЖНО ПОЛУЧИМОЕ СЕРДЕЧКО!!! Делай скриншот и отпрвляй @KAPAC1D !",
            ],
            weights=[
                0.12,
                0.12,
                0.12,
                0.12,
                0.10,
                0.10,
                0.10,
                0.04,
                0.04,
                0.04,
                0.02,
                0.02,
                0.01,
                0.01,
                0.01,
                0.008,
                0.008,
                0.008,
                0.0025,
                0.0025,
                0.001,
            ],
            k=1,
        )
        bot.edit_message_text(
            f"Вам выпало: {result[0]}", call.message.chat.id, call.message.message_id
        )
    if call.data == "but2":
        mainmenu = types.InlineKeyboardMarkup()
        key3 = types.InlineKeyboardButton(text="Назад", callback_data="but3")
        mainmenu.add(key3)
        bot.edit_message_text(
            """Шансы:
        Обычное сердечко - 48%
        Необычное сердечко - 30%
        Редкое сердечко - 12%
        Очень редкое сердечко - 4%
        Эпическое сердечко - 3%
        Мифическое сердечко - 2.4%
        Легендарное сердечко - 0.5%
        Невозможное сердечко - 0.1%""",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=mainmenu,
        )
    if call.data == "but3":
        mainmenu = types.InlineKeyboardMarkup()
        key1 = types.InlineKeyboardButton(
            text="Получить сердечко", callback_data="but1"
        )
        key2 = types.InlineKeyboardButton(text="Шансы", callback_data="but2")
        mainmenu.add(key1, key2)
        bot.edit_message_text(
            hearts, call.message.chat.id, call.message.message_id, reply_markup=mainmenu
        )


@bot.message_handler(commands=["feedback"])
def get_text_messages_(message: Message):
    if message.from_user is not None:
        add_or_update_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
        bot.send_message(
            message.from_user.id,
            """Напишите ЗДЕСЬ, что хотите добавить автору (@KAPAC1D) .""",
        )
        users_states[message.from_user.id] = UsersStates.FEEDBACKKING


@bot.message_handler(commands=["stats"])
def handle_stats(message):
    if message.from_user is not None:
        add_or_update_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
        log_event(message.from_user.id, "stats")
    cnt = get_user_count()
    bot.reply_to(message, f"Всего пользователей: {cnt}")


@bot.message_handler(commands=["users"])
def handle_users(message):
    if message.from_user.id not in admins:
        return
    if message.from_user is not None:
        add_or_update_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
        # Для безопасности можно ограничить, например, по ID админа
        log_event(message.from_user.id, "users")
    users = get_all_users()
    if not users:
        bot.reply_to(message, "Пока ни одного пользователя.")
        return
    lines = []
    for uid, uname, fname in users:
        lines.append(f"• {fname} (@{uname or 'нет'}) ")
    bot.reply_to(message, "Список пользователей:\n" + "\n".join(lines))


@bot.message_handler()
def handle_text(message: Message):
    if (
        message.from_user is not None
        and message.text is not None
        and users_states.get(message.from_user.id, UsersStates.DEFAULT)
        == UsersStates.FEEDBACKKING
    ):
        bot.send_message(
            admins[0],
            f"Доставлено новое сообщение от {message.from_user.full_name} (@{message.from_user.username or 'нет'}):\n"
            + message.text,
        )
        bot.send_message(message.from_user.id, "Успешно доставлено.")
        users_states[message.from_user.id] = UsersStates.DEFAULT


print("bot is starting...")
bot.polling(none_stop=True, interval=0)
