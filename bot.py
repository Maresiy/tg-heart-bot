import os
import random

import telebot
from dotenv import load_dotenv
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# Загружаем переменные из .env
load_dotenv()

# Получаем значение TOKEN
token = os.getenv("TOKEN") or ""

bot = telebot.TeleBot(token)
print(token)
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
        text="Запустить бота ДА/НЕТ от этого автора.", url="https://t.me/DA_HET_bot"
    )
    mainmenu.add(key0)
    bot.send_message(
        message.from_user.id,
        """Здравствуйте!\n
Этот бот создан пользователем @KAPAC1D в 2026 году.\n
Он выбирает ваше cердечко на данный день. Для запуска нажмите Menu и выберите функцию. Также есть у нас ещё бот:""",
        reply_markup=mainmenu,
    )


@bot.message_handler(commands=["heart"])
def get_text_messages(message: Message):
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
                0.11,
                0.11,
                0.11,
                0.11,
                0.09,
                0.09,
                0.09,
                0.05,
                0.05,
                0.05,
                0.03,
                0.03,
                0.015,
                0.015,
                0.015,
                0.008,
                0.008,
                0.008,
                0.0045,
                0.0045,
                0.002,
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
        Обычное сердечко - 44%
        Необычное сердечко - 27%
        Редкое сердечко - 15%
        Очень редкое сердечко - 6%
        Эпическое сердечко - 4.5%
        Мифическое сердечко - 2.4%
        Легендарное сердечко - 0.9%
        Невозможное сердечко - 0.2%""",
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


@bot.message_handler(commands=["OT3blB"])
def get_text_messages_(message: Message):
    if message.from_user is not None:
        bot.send_message(
            message.from_user.id, """Напишите, что хотите добавить @RufiColumbae."""
        )


bot.polling(none_stop=True, interval=0)
