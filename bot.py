import os
import sys
import threading
import time
from enum import Enum

import schedule
import telebot
from dotenv import load_dotenv
from telebot import apihelper, types
from telebot.types import Message

from db import (
    Achievement,
    SessionLocal,
    UserAchievement,
    add_heart_to_collection,
    add_heart_win,  # ← новая функция
    add_or_update_user,
    add_referral_bonus,
    add_xp,
    check_and_unlock_achievements,
    claim_bonus_code,
    claim_daily_bonus,
    claim_subscription_bonus,
    create_duel,
    decline_duel,
    decrement_attempt,
    ensure_daily_quests,
    get_all_users,
    get_attempts_left,
    get_available_opponents,
    get_duel_by_id,
    get_leaderboard_collection,
    get_leaderboard_legendary,
    get_leaderboard_total_hearts,
    get_leaderboard_xp,
    get_referral_link,
    get_top_legendary_users,  # ← новая функция
    get_top_xp_users,
    get_user_achievements,  # если нужна функция, добавьте её ниже
    get_user_by_telegram_id,
    get_user_collection,
    get_user_count,
    get_user_profile,
    has_won_today,
    init_achievements,
    init_db,
    log_event,
    process_referral,
    reset_daily_attempts,
    resolve_duel,
    select,
    update_quest_progress,
)
from hearts import hearts_pool

# Загружаем переменные из .env
_ = load_dotenv()

# Получаем значение TOKEN
token = os.getenv("TOKEN") or ""
if not token:
    print("TOKEN not found in .env")
    sys.exit(0)

proxy = os.getenv("PROXY") or ""
if proxy:
    print("PROXY found in .env")
    apihelper.proxy = {"http": proxy, "https": proxy}


def run_scheduler():
    schedule.every().day.at("15:30").do(reset_daily_attempts)
    while True:
        schedule.run_pending()
        time.sleep(60)


def notify_legendary_win(
    user: types.User, heart_character: str, win_description: str
) -> None:
    """Отправить сообщение в канал о легендарной/невозможной победе."""
    try:
        text = (
            f"🎉 <b>Новый трофей!</b>\n"
            f"Пользователь <b>{user.full_name}</b> (@{user.username or 'нет'}) "
            f"получил сердечко: {heart_character}\n"
            f"Описание: {win_description}"
        )
        bot.send_message(f"@{CHANNEL_USERNAME}", text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка отправки в канал: {e}")


scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

init_db()
init_achievements()


class UsersStates(Enum):
    DEFAULT = 1
    FEEDBACKKING = 2


CHANNEL_USERNAME = "channel_evoworld"
XP_BY_CHARACTER = {
    "❤️‍🩹": 1,
    "🩷": 1,
    "🖤": 1,
    "💜": 1,
    "🩶": 2,
    "🤍": 2,
    "🤎": 2,
    "💛": 5,
    "🧡": 5,
    "❤️": 5,
    "🩵": 10,
    "💙": 10,
    "💕": 20,
    "💞": 20,
    "💘": 20,
    "💓": 40,
    "💗": 40,
    "💖": 40,
    "💝": 100,
    "❣️": 100,
    "❤️‍🔥": 500,
}
admin = int(os.getenv("ADMIN") or "0")
admins = [admin] if admin else []
users_states: dict[int, UsersStates] = {}

bot = telebot.TeleBot(token)

# Получаем username бота для реферальных ссылок (может быть недоступно до запуска)


def register_user(message_or_call: types.Message | types.CallbackQuery) -> None:
    """Регистрирует пользователя в БД, если его ещё нет."""
    user = message_or_call.from_user
    if user is None:
        return
    add_or_update_user(user.id, user.username, user.full_name)


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
def start(message: Message):
    user = message.from_user
    if user is None:
        return

    # Проверяем реферальный параметр
    referrer_id = None
    parts = message.text.split() if message.text else []
    if len(parts) > 1 and parts[1].startswith("ref_"):
        try:
            referrer_id = int(parts[1][4:])
        except ValueError:
            pass

    existing_user = get_user_by_telegram_id(user.id)
    ref_success = False  # ← инициализация
    ref_msg = ""  # можно и пустую строку

    if existing_user is None and referrer_id is not None:
        ref_success, ref_msg = process_referral(user.id, referrer_id)

    # Регистрируем пользователя
    register_user(message)

    # Если новый пользователь пришёл по реферальной ссылке и рефереру начислен бонус
    if existing_user is None and referrer_id is not None and ref_success:
        add_referral_bonus(user.id, referrer_id)
        # Проверяем достижения для нового пользователя и пригласившего
        check_and_unlock_achievements(user.id)
        check_and_unlock_achievements(referrer_id)
        # ... дополнительная логика

    # Остальное приветствие
    mainmenu = types.InlineKeyboardMarkup()
    key0 = types.InlineKeyboardButton(
        text="Запустить бота ДА/НЕТ от этого автора.(пока не работает)",
        url="https://t.me/DA_HET_bot",
    )
    mainmenu.add(key0)
    bot.send_message(
        user.id,
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


@bot.message_handler(commands=["profile"])
def handle_profile(message: Message):
    register_user(message)
    if message.from_user is None:
        return
    profile = get_user_profile(message.from_user.id)
    if profile is None:
        bot.reply_to(message, "Сначала отправьте /start")
        return
    level, xp, attempts = profile
    # Если нужно вычислить до следующего уровня:
    # next_level_xp = (level) ** 2 * 100
    bot.reply_to(
        message,
        f"📊 Ваш профиль:\nУровень: {level}\nОпыт: {xp} XP\nПопытки: {attempts}",
    )


@bot.callback_query_handler(func=lambda _: True)
def callback_inline(call):

    if call.data == "but1":
        if not decrement_attempt(call.from_user.id):
            bot.answer_callback_query(
                call.id, "У тебя закончились попытки 😢", show_alert=True
            )
            return

        # 2. Получение сердечка
        result = hearts_pool.get_random()

        # 3. Добавляем в коллекцию (ОДИН раз, всегда)
        add_heart_to_collection(call.from_user.id, result.character)

        # 4. Если легендарное/невозможное — сохраняем и уведомляем в канал
        if result.character in ["💝", "❣️", "❤️‍🔥"]:
            add_heart_win(call.from_user.id, result.character, result.win_description)
            try:
                bot.send_message(
                    f"@{CHANNEL_USERNAME}",
                    f"🎉 Пользователь {call.from_user.full_name} (@{call.from_user.username or 'нет'}) получил {result.character} - {result.win_description}",
                    parse_mode="HTML",
                )
            except Exception as e:
                print(f"Не удалось отправить в канал: {e}")

        # 5. Начисление XP (один раз)
        xp_amount = XP_BY_CHARACTER.get(result.character, 0)
        level_up_msg = add_xp(call.from_user.id, xp_amount)

        # 6. Обновляем задания (всегда)
        ensure_daily_quests(call.from_user.id)
        update_quest_progress(call.from_user.id, "collect_10", 1)
        if result.character in ["💝", "❣️", "❤️‍🔥"]:
            update_quest_progress(call.from_user.id, "collect_legendary", 1)

        # 7. Проверяем достижения (всегда)
        new_ach = check_and_unlock_achievements(call.from_user.id)
        if new_ach:
            names = ", ".join(new_ach)
            bot.answer_callback_query(
                call.id, f"🏅 Достижения: {names}!", show_alert=True
            )

        # 8. Сообщение с результатом
        bot.edit_message_text(
            f"Вам выпало: {result.character} - {result.win_description} "
            f"с шансом {100 * result.weight / hearts_pool.get_weights_sum()}%",
            call.message.chat.id,
            call.message.message_id,
        )

        # 9. Уведомление о повышении уровня (если есть)
        if level_up_msg:
            bot.answer_callback_query(call.id, level_up_msg, show_alert=True)

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

    if call.data == "check_subscription":
        user_id = call.from_user.id
        try:
            member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
            if member.status in ["member", "administrator", "creator"]:
                success, msg = claim_subscription_bonus(user_id)
                if success:
                    bot.answer_callback_query(call.id, msg)
                    bot.edit_message_text(
                        "Поздравляем! Вы получили +10 попыток.",
                        call.message.chat.id,
                        call.message.message_id,
                    )
                else:
                    bot.answer_callback_query(call.id, msg, show_alert=True)
            else:
                bot.answer_callback_query(
                    call.id,
                    "Вы ещё не подписались на канал. Подпишитесь и попробуйте снова.",
                    show_alert=True,
                )
        except Exception as e:
            print(f"Ошибка проверки подписки: {e}")
            bot.answer_callback_query(
                call.id,
                "Не удалось проверить подписку. Попробуйте позже.",
                show_alert=True,
            )
            if call.data == "leaderboard_xp":
                top = get_leaderboard_xp(10)
                text = "🏆 Топ по XP:\n"
                for i, (user, xp) in enumerate(top, start=1):
                    text += (
                        f"{i}. {user.full_name} (@{user.username or 'нет'}) — {xp} XP\n"
                    )
                bot.edit_message_text(
                    text, call.message.chat.id, call.message.message_id
                )
            elif call.data == "leaderboard_hearts":
                top = get_leaderboard_total_hearts(10)
                text = "❤️ Топ по общему количеству сердечек:\n"
                for i, (user, total) in enumerate(top, start=1):
                    text += f"{i}. {user.full_name} (@{user.username or 'нет'}) — {total} шт.\n"
                bot.edit_message_text(
                    text, call.message.chat.id, call.message.message_id
                )
            elif call.data == "leaderboard_legendary":
                top = get_leaderboard_legendary(10)
                text = "💎 Топ по легендарным и невозможным сердечкам:\n"
                for i, (user, total) in enumerate(top, start=1):
                    text += f"{i}. {user.full_name} (@{user.username or 'нет'}) — {total} шт.\n"
                bot.edit_message_text(
                    text, call.message.chat.id, call.message.message_id
                )
            elif call.data == "leaderboard_collection":
                top = get_leaderboard_collection(10)
                text = "📦 Топ по уникальным сердечкам в коллекции:\n"
                for i, (user, unique) in enumerate(top, start=1):
                    text += f"{i}. {user.full_name} (@{user.username or 'нет'}) — {unique} видов\n"
                bot.edit_message_text(
                    text, call.message.chat.id, call.message.message_id
                )
    if call.data.startswith("challenge:"):
        opponent_id = int(call.data.split(":")[1])
        challenger_id = call.from_user.id

        if has_won_today(challenger_id):
            bot.answer_callback_query(
                call.id, "Вы уже победили сегодня!", show_alert=True
            )
            return

        success, result = create_duel(challenger_id, opponent_id)
        if not success:
            bot.answer_callback_query(call.id, str(result), show_alert=True)
            return
        duel_id = result

        opponent_user = get_user_by_telegram_id(opponent_id)
        if opponent_user:
            keyboard = types.InlineKeyboardMarkup()
            accept_btn = types.InlineKeyboardButton(
                "Принять", callback_data=f"accept_duel:{duel_id}"
            )
            decline_btn = types.InlineKeyboardButton(
                "Отклонить", callback_data=f"decline_duel:{duel_id}"
            )
            keyboard.add(accept_btn, decline_btn)
            bot.send_message(
                opponent_id,
                f"⚔️ {call.from_user.full_name} вызывает вас на дуэль!",
                reply_markup=keyboard,
            )
            bot.answer_callback_query(call.id, "Вызов отправлен!")
        else:
            bot.answer_callback_query(
                call.id, "Не удалось найти соперника.", show_alert=True
            )

    if call.data.startswith("accept_duel:"):
        duel_id = int(call.data.split(":")[1])
        result_msg = resolve_duel(duel_id)
        duel = get_duel_by_id(duel_id)
        if duel:
            # Если нажал инициатор, отправляем сообщение оппоненту
            if call.from_user.id == duel.challenger_id:
                bot.send_message(duel.opponent_id, result_msg)
            else:
                # Если нажал оппонент, отправляем сообщение инициатору
                bot.send_message(duel.challenger_id, result_msg)

            # Редактируем сообщение с кнопками у нажавшего (результат виден там)
            bot.edit_message_text(
                result_msg, call.message.chat.id, call.message.message_id
            )

            # Проверяем достижения для обоих
            new_ach = check_and_unlock_achievements(call.from_user.id)
            if new_ach:
                names = ", ".join(new_ach)
                bot.answer_callback_query(
                    call.id, f"🏅 Достижения: {names}!", show_alert=True
                )
                new_ach = check_and_unlock_achievements(duel.challenger_id)
                if new_ach:
                    bot.send_message(
                        duel.challenger_id, "🏅 Новые достижения: " + ", ".join(new_ach)
                    )
        else:
            bot.answer_callback_query(
                call.id, "Ошибка: дуэль не найдена.", show_alert=True
            )

    if call.data.startswith("decline_duel:"):
        duel_id = int(call.data.split(":")[1])
        result_msg = decline_duel(duel_id)
        duel = get_duel_by_id(duel_id)
        if duel:
            bot.send_message(duel.challenger_id, "Ваш вызов был отклонён.")
            bot.edit_message_text(
                "❌ Дуэль отклонена.",
                call.message.chat.id,
                call.message.message_id,
            )
        else:
            bot.answer_callback_query(
                call.id, "Ошибка: дуэль не найдена.", show_alert=True
            )
    if call.data == "leaderboard_xp":
        top = get_leaderboard_xp(10)
        text = "🏆 Топ по XP:\n"
        for i, (user, xp) in enumerate(top, start=1):
            text += f"{i}. {user.full_name} (@{user.username or 'нет'}) — {xp} XP\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

    elif call.data == "leaderboard_hearts":
        top = get_leaderboard_total_hearts(10)
        text = "❤️ Топ по общему количеству сердечек:\n"
        for i, (user, total) in enumerate(top, start=1):
            text += f"{i}. {user.full_name} (@{user.username or 'нет'}) — {total} шт.\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

    elif call.data == "leaderboard_legendary":
        top = get_leaderboard_legendary(10)
        text = "💎 Топ по легендарным и невозможным сердечкам:\n"
        for i, (user, total) in enumerate(top, start=1):
            text += f"{i}. {user.full_name} (@{user.username or 'нет'}) — {total} шт.\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

    elif call.data == "leaderboard_collection":
        top = get_leaderboard_collection(10)
        text = "📦 Топ по уникальным сердечкам в коллекции:\n"
        for i, (user, unique) in enumerate(top, start=1):
            text += (
                f"{i}. {user.full_name} (@{user.username or 'нет'}) — {unique} видов\n"
            )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)


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


def get_subscribe_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    # Кнопка-ссылка на канал
    url_btn = types.InlineKeyboardButton(
        text="📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}"
    )
    # Кнопка проверки подписки
    check_btn = types.InlineKeyboardButton(
        text="✅ Проверить подписку", callback_data="check_subscription"
    )
    keyboard.add(url_btn)
    keyboard.add(check_btn)
    return keyboard


@bot.message_handler(commands=["bonus"])
def handle_bonus(message: Message):
    register_user(message)  # на всякий случай регистрируем
    if message.from_user is not None:
        bot.send_message(
            message.from_user.id,
            "Подпишитесь на наш канал и получите +10 попыток!",
            reply_markup=get_subscribe_keyboard(),
        )


@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check_subscription(call: types.CallbackQuery):
    user_id = call.from_user.id

    # Проверяем подписку через Bot API
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        # Допустимые статусы: участник, администратор, создатель
        if member.status in ["member", "administrator", "creator"]:
            success, msg = claim_subscription_bonus(user_id)
            if success:
                bot.answer_callback_query(call.id, msg)
                # Обновим сообщение, убрав кнопки
                if call.message is not None:
                    bot.edit_message_text(
                        "Поздравляем! Вы получили +10 попыток.",
                        call.message.chat.id,
                        call.message.message_id,
                    )
                else:
                    # Если сообщение недоступно, отправляем новое или используем answer_callback_query
                    bot.answer_callback_query(
                        call.id,
                        "Поздравляем! Вы получили +10 попыток.",
                        show_alert=True,
                    )

            else:
                bot.answer_callback_query(call.id, msg, show_alert=True)
        else:
            bot.answer_callback_query(
                call.id,
                "Вы ещё не подписались на канал. Подпишитесь и попробуйте снова.",
                show_alert=True,
            )
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        bot.answer_callback_query(
            call.id,
            "Не удалось проверить подписку. Убедитесь, что бот является администратором канала (если канал приватный) или канал публичный.",
            show_alert=True,
        )


@bot.message_handler(commands=["redeem"])
def handle_redeem(message: Message):
    # Проверяем, что после команды есть текст (сам код)
    if message.text is not None and message.from_user is not None:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /redeem <код>")
            return
        code = parts[1].strip()
        success, msg = claim_bonus_code(message.from_user.id, code)
        bot.reply_to(message, msg)


@bot.message_handler(commands=["daily"])
def handle_daily(message: Message):
    register_user(message)  # убедимся, что пользователь в базе
    if message.text is not None and message.from_user is not None:
        success, msg = claim_daily_bonus(message.from_user.id)
        bot.reply_to(message, msg)


@bot.message_handler(commands=["referral"])
def handle_referral(message: Message):
    register_user(message)
    if message.text is not None and message.from_user is not None:
        link = f"https://t.me/eight_of_march_heart_bot?start=ref_{message.from_user.id}"
        bot.reply_to(
            message,
            f"Ваша персональная ссылка для приглашения друзей:\n{link}\n\n"
            f"За каждого приглашённого друга (если он новый пользователь) вы оба получите +10 попыток!",
        )


@bot.message_handler(commands=["collection"])
def handle_collection(message: Message):
    register_user(message)
    if message.from_user is not None:
        collection = get_user_collection(message.from_user.id)
        if not collection:
            bot.reply_to(message, "У вас пока нет сердечек в коллекции.")
            return
        lines = [f"{item.heart_character} x{item.count}" for item in collection]
        bot.reply_to(message, "Ваша коллекция:\n" + "\n".join(lines))


@bot.message_handler(commands=["achievements"])
def handle_achievements(message: Message):
    register_user(message)
    user_ach = {}  # ← инициализация пустым словарём
    with SessionLocal() as session:
        all_ach = session.scalars(select(Achievement)).all()
        if message.from_user is not None:
            user_ach = {
                ua.achievement_id: ua
                for ua in session.scalars(
                    select(UserAchievement).where(
                        UserAchievement.user_id == message.from_user.id
                    )
                ).all()
            }
        lines = []
        for ach in all_ach:
            if ach.id in user_ach:
                status = "✅"
            else:
                status = "⬜"
            lines.append(
                f"{status} {ach.name} — {ach.description} (награда: {ach.reward_amount} {ach.reward_type})"
            )
        bot.reply_to(message, "Достижения:\n" + "\n".join(lines))


@bot.message_handler(commands=["duel"])
def handle_duel(message: Message):
    if message.text is None:
        return
    register_user(message)
    user = message.from_user
    if user is None:
        return

    if has_won_today(user.id):
        bot.reply_to(message, "Вы уже одержали победу сегодня! Возвращайтесь завтра.")
        return

    opponents = get_available_opponents(user.id)
    if not opponents:
        bot.reply_to(
            message, "Сегодня нет доступных соперников. Все уже сражались или победили."
        )
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for opp in opponents:
        name = opp.full_name or "Пользователь"
        keyboard.add(
            types.InlineKeyboardButton(
                text=name, callback_data=f"challenge:{opp.telegram_id}"
            )
        )

    bot.reply_to(message, "Выберите соперника для дуэли:", reply_markup=keyboard)


@bot.message_handler(commands=["leaderboard"])
def handle_leaderboard(message: Message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("🏆 Топ по XP", callback_data="leaderboard_xp"),
        types.InlineKeyboardButton(
            "❤️ Топ по сердечкам", callback_data="leaderboard_hearts"
        ),
        types.InlineKeyboardButton(
            "💎 Топ по легендарным", callback_data="leaderboard_legendary"
        ),
        types.InlineKeyboardButton(
            "📦 Топ по коллекции", callback_data="leaderboard_collection"
        ),
    )
    bot.reply_to(message, "Выберите категорию:", reply_markup=keyboard)


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
