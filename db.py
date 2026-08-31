from datetime import UTC, date, datetime, timedelta
from typing import TypedDict

from sqlalchemy import create_engine, func, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

# Для многопоточного доступа (бот + планировщик)
engine = create_engine(
    "sqlite:///bot.db", echo=False, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str | None] = mapped_column(default=None)
    full_name: Mapped[str] = mapped_column(default="")
    first_seen: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    attempts_left: Mapped[int] = mapped_column(default=10)
    xp: Mapped[int] = mapped_column(default=0)
    bonus_claimed: Mapped[bool] = mapped_column(default=False)
    bonus_code_claimed: Mapped[bool] = mapped_column(default=False)
    last_daily_bonus_date: Mapped[date | None] = mapped_column(default=None)
    daily_streak: Mapped[int] = mapped_column(default=0)
    referred_by: Mapped[int | None] = mapped_column(default=None)


class StatEvent(Base):
    __tablename__ = "stat_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(default=0)
    event: Mapped[str] = mapped_column(default="")
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class HeartWin(Base):
    __tablename__ = "heart_wins"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(default=0)
    heart_character: Mapped[str] = mapped_column(default="")
    win_description: Mapped[str] = mapped_column(default="")
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class UserQuest(Base):
    __tablename__ = "user_quests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(default=0, index=True)
    quest_type: Mapped[str] = mapped_column(default="")
    progress: Mapped[int] = mapped_column(default=0)
    target: Mapped[int] = mapped_column(default=1)
    completed: Mapped[bool] = mapped_column(default=False)
    date_: Mapped[date] = mapped_column(default=lambda: datetime.now(UTC).date())


class Duel(Base):
    __tablename__ = "duels"

    id: Mapped[int] = mapped_column(primary_key=True)
    challenger_id: Mapped[int] = mapped_column(default=0)
    opponent_id: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="pending")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    challenger_heart: Mapped[str | None] = mapped_column(default=None)
    opponent_heart: Mapped[str | None] = mapped_column(default=None)
    winner_id: Mapped[int | None] = mapped_column(default=None)


class UserHeart(Base):
    __tablename__ = "user_hearts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(default=0, index=True)
    heart_character: Mapped[str] = mapped_column(default="")
    count: Mapped[int] = mapped_column(default=0)


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(default="")
    description: Mapped[str] = mapped_column(default="")
    condition_type: Mapped[str] = mapped_column(default="")
    condition_value: Mapped[int] = mapped_column(default=0)
    reward_type: Mapped[str] = mapped_column(default="")
    reward_amount: Mapped[int] = mapped_column(default=0)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(default=0, index=True)
    achievement_id: Mapped[int] = mapped_column(default=0)
    unlocked_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


# ---------------------------- Функции инициализации ----------------------------
def init_db():
    """Создать таблицы, если их ещё нет."""
    Base.metadata.create_all(bind=engine)


def log_event(telegram_id: int, event: str) -> None:
    """Записать событие в статистику."""
    with SessionLocal() as session:
        ev = StatEvent(user_id=telegram_id, event=event)
        session.add(ev)
        session.commit()


QUEST_DESCRIPTIONS = {
    "collect_10": "Получить 10 любых сердечек",
    "collect_legendary": "Получить легендарное или невозможное сердечко",
    "daily_login": "Зайти в бота (отправить любую команду)",
}


def init_achievements():
    """Создать стандартные достижения, если таблица пуста."""
    achievements_data = [
        (
            "first_heart",
            "Первое сердечко",
            "Получите первое сердечко",
            "total_hearts",
            1,
            "attempts",
            3,
        ),
        (
            "collect_100",
            "Сотня сердец",
            "Соберите 100 сердечек",
            "total_hearts",
            100,
            "xp",
            500,
        ),
        (
            "collect_500",
            "Полтысячи",
            "Соберите 500 сердечек",
            "total_hearts",
            500,
            "xp",
            2000,
        ),
        (
            "legendary_1",
            "Легенда",
            "Получите легендарное сердечко",
            "legendary_hearts",
            1,
            "attempts",
            10,
        ),
        (
            "legendary_10",
            "Охотник за легендами",
            "Получите 10 легендарных сердечек",
            "legendary_hearts",
            10,
            "xp",
            1000,
        ),
        (
            "impossible_1",
            "Невозможное возможно",
            "Получите невозможно получимое сердечко",
            "impossible_hearts",
            1,
            "attempts",
            50,
        ),
        (
            "level_5",
            "5-й уровень",
            "Достигните 5 уровня",
            "xp_level",
            5,
            "attempts",
            15,
        ),
        (
            "level_10",
            "10-й уровень",
            "Достигните 10 уровня",
            "xp_level",
            10,
            "xp",
            2000,
        ),
        (
            "duel_win_1",
            "Первая победа",
            "Победите в дуэли",
            "duel_wins",
            1,
            "attempts",
            5,
        ),
        (
            "duel_win_5",
            "Мастер дуэлей",
            "Победите в 5 дуэлях",
            "duel_wins",
            5,
            "xp",
            1500,
        ),
        (
            "referral_1",
            "Друг пришёл",
            "Пригласите друга",
            "referral_count",
            1,
            "attempts",
            10,
        ),
        (
            "referral_5",
            "Вербовщик",
            "Пригласите 5 друзей",
            "referral_count",
            5,
            "xp",
            2000,
        ),
        (
            "collection_10",
            "Коллекционер",
            "Соберите 10 разных сердечек",
            "collection_count",
            10,
            "attempts",
            20,
        ),
        (
            "collection_21",
            "Полная коллекция",
            "Соберите все 21 вид сердечек",
            "collection_count",
            21,
            "xp",
            5000,
        ),
    ]
    with SessionLocal() as session:
        if not session.scalars(select(Achievement)).first():
            for code, name, desc, ctype, cval, rtype, ramount in achievements_data:
                session.add(
                    Achievement(
                        code=code,
                        name=name,
                        description=desc,
                        condition_type=ctype,
                        condition_value=cval,
                        reward_type=rtype,
                        reward_amount=ramount,
                    )
                )
            session.commit()


# ---------------------------- Работа с пользователями ----------------------------
def add_or_update_user(telegram_id: int, username: str | None, full_name: str) -> None:
    with SessionLocal() as session:
        user = session.scalars(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if user:
            user.username = username
            user.full_name = full_name
        else:
            user = User(telegram_id=telegram_id, username=username, full_name=full_name)
            session.add(user)
        session.commit()


def get_user_by_telegram_id(telegram_id: int) -> User | None:
    with SessionLocal() as session:
        return session.scalars(
            select(User).where(User.telegram_id == telegram_id)
        ).first()


def get_user_count() -> int:
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(User)) or 0


def get_all_users() -> list[tuple[int, str | None, str]]:
    with SessionLocal() as session:
        result = session.execute(
            select(User.telegram_id, User.username, User.full_name)
        )
        return [tuple(row) for row in result]


def get_attempts_left(telegram_id: int) -> int:
    with SessionLocal() as session:
        user = session.scalars(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        return user.attempts_left if user else 0


def decrement_attempt(telegram_id: int) -> bool:
    with SessionLocal() as session:
        user = session.scalars(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if not user or user.attempts_left <= 0:
            return False
        user.attempts_left -= 1
        session.commit()
        return True


def reset_attempts_for_user(telegram_id: int, new_attempts: int = 10) -> None:
    with SessionLocal() as session:
        _ = session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(attempts_left=new_attempts)
        )
        session.commit()


def reset_daily_attempts() -> None:
    with SessionLocal() as session:
        _ = session.execute(
            update(User).where(User.attempts_left < 10).values(attempts_left=10)
        )
        session.commit()


# ---------------------------- XP и уровни ----------------------------
def get_level_from_xp(xp: int) -> int:
    import math

    if xp < 0:
        return 0
    return int(math.sqrt(xp // 100)) + 1


def add_xp(telegram_id: int, amount: int) -> str | None:
    with SessionLocal() as session:
        user = session.scalars(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if not user:
            return None
        old_level = get_level_from_xp(user.xp)
        user.xp += amount
        new_level = get_level_from_xp(user.xp)
        session.commit()
        if new_level > old_level:
            user.attempts_left += 5
            session.commit()
            return f"🎉 Поздравляем! Вы достигли {new_level} уровня! Вам начислено +5 попыток."
        return None


def get_user_profile(telegram_id: int) -> tuple[int, int, int] | None:
    with SessionLocal() as session:
        user = session.scalars(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if not user:
            return None
        level = get_level_from_xp(user.xp)
        return level, user.xp, user.attempts_left


# ---------------------------- Коллекция и сердечки ----------------------------
def add_heart_to_collection(user_id: int, heart_character: str) -> None:
    with SessionLocal() as session:
        record = session.scalars(
            select(UserHeart).where(
                UserHeart.user_id == user_id,
                UserHeart.heart_character == heart_character,
            )
        ).first()
        if record:
            record.count += 1
        else:
            new_record = UserHeart(
                user_id=user_id, heart_character=heart_character, count=1
            )
            session.add(new_record)
        session.commit()


def get_user_collection(user_id: int) -> list[UserHeart]:
    with SessionLocal() as session:
        return list(
            session.scalars(select(UserHeart).where(UserHeart.user_id == user_id)).all()
        )


def add_heart_win(user_id: int, heart_character: str, win_description: str) -> None:
    with SessionLocal() as session:
        win = HeartWin(
            user_id=user_id,
            heart_character=heart_character,
            win_description=win_description,
        )
        session.add(win)
        session.commit()


# ---------------------------- Ежедневные задания ----------------------------
def ensure_daily_quests(user_id: int) -> None:
    today = datetime.now(UTC).date()
    with SessionLocal() as session:
        existing = session.scalars(
            select(UserQuest).where(
                UserQuest.user_id == user_id, UserQuest.date_ == today
            )
        ).all()
        if not existing:
            quests = [
                UserQuest(user_id=user_id, quest_type="collect_10", target=10),
                UserQuest(user_id=user_id, quest_type="collect_legendary", target=1),
                UserQuest(user_id=user_id, quest_type="daily_login", target=1),
            ]
            session.add_all(quests)
            session.commit()


def update_quest_progress(
    user_id: int, quest_type: str, increment: int = 1
) -> str | None:
    today = datetime.now(UTC).date()
    with SessionLocal() as session:
        quest = session.scalars(
            select(UserQuest).where(
                UserQuest.user_id == user_id,
                UserQuest.quest_type == quest_type,
                UserQuest.date_ == today,
                UserQuest.completed == False,
            )
        ).first()
        if not quest:
            return None
        quest.progress += increment
        if quest.progress >= quest.target:
            quest.completed = True
            session.commit()
            user = session.scalars(
                select(User).where(User.telegram_id == user_id)
            ).first()
            if user:
                user.attempts_left += 5
                user.xp += 50
                session.commit()
                return f"✅ Задание «{QUEST_DESCRIPTIONS.get(quest_type, '')}» выполнено! Награда: +5 попыток, +50 XP."
        session.commit()
        return None


def get_daily_quests(user_id: int, day: date) -> list[UserQuest]:
    with SessionLocal() as session:
        return list(
            session.scalars(
                select(UserQuest).where(
                    UserQuest.user_id == user_id, UserQuest.date_ == day
                )
            ).all()
        )


# ---------------------------- Достижения ----------------------------
class UserStats(TypedDict):
    total_hearts: int
    legendary_hearts: int
    impossible_hearts: int
    xp_level: int
    duel_wins: int
    referral_count: int
    collection_count: int


def get_user_stats(user_id: int) -> UserStats | dict[str, int]:
    with SessionLocal() as session:
        user = session.scalars(select(User).where(User.telegram_id == user_id)).first()
        if not user:
            return {}
        total_hearts = (
            session.scalar(
                select(func.sum(UserHeart.count)).where(UserHeart.user_id == user_id)
            )
            or 0
        )
        legendary_hearts = (
            session.scalar(
                select(func.sum(UserHeart.count)).where(
                    UserHeart.user_id == user_id,
                    UserHeart.heart_character.in_(["💝", "❣️", "❤️‍🔥"]),
                )
            )
            or 0
        )
        impossible_hearts = (
            session.scalar(
                select(func.sum(UserHeart.count)).where(
                    UserHeart.user_id == user_id, UserHeart.heart_character == "❤️‍🔥"
                )
            )
            or 0
        )
        xp_level = get_level_from_xp(user.xp)
        duel_wins = (
            session.scalar(
                select(func.count())
                .select_from(Duel)
                .where(Duel.winner_id == user_id, Duel.status == "completed")
            )
            or 0
        )
        referral_count = (
            session.scalar(
                select(func.count())
                .select_from(User)
                .where(User.referred_by == user_id)
            )
            or 0
        )
        collection_count = (
            session.scalar(
                select(func.count())
                .select_from(UserHeart)
                .where(UserHeart.user_id == user_id, UserHeart.count > 0)
            )
            or 0
        )
        return {
            "total_hearts": total_hearts,
            "legendary_hearts": legendary_hearts,
            "impossible_hearts": impossible_hearts,
            "xp_level": xp_level,
            "duel_wins": duel_wins,
            "referral_count": referral_count,
            "collection_count": collection_count,
        }


def check_and_unlock_achievements(user_id: int) -> list[str]:
    stats = get_user_stats(user_id)
    if not stats:
        return []
    with SessionLocal() as session:
        all_ach = session.scalars(select(Achievement)).all()
        unlocked_ids = set(
            session.scalars(
                select(UserAchievement.achievement_id).where(
                    UserAchievement.user_id == user_id
                )
            ).all()
        )
        new_unlocked_names = []
        for ach in all_ach:
            if ach.id in unlocked_ids:
                continue
            condition_met = False
            if ach.condition_type == "total_hearts":
                condition_met = stats["total_hearts"] >= ach.condition_value
            elif ach.condition_type == "legendary_hearts":
                condition_met = stats["legendary_hearts"] >= ach.condition_value
            elif ach.condition_type == "impossible_hearts":
                condition_met = stats["impossible_hearts"] >= ach.condition_value
            elif ach.condition_type == "xp_level":
                condition_met = stats["xp_level"] >= ach.condition_value
            elif ach.condition_type == "duel_wins":
                condition_met = stats["duel_wins"] >= ach.condition_value
            elif ach.condition_type == "referral_count":
                condition_met = stats["referral_count"] >= ach.condition_value
            elif ach.condition_type == "collection_count":
                condition_met = stats["collection_count"] >= ach.condition_value

            if condition_met:
                session.add(UserAchievement(user_id=user_id, achievement_id=ach.id))
                new_unlocked_names.append(ach.name)
                user = session.scalars(
                    select(User).where(User.telegram_id == user_id)
                ).first()
                if user:
                    if ach.reward_type == "attempts":
                        user.attempts_left += ach.reward_amount
                    elif ach.reward_type == "xp":
                        user.xp += ach.reward_amount
        session.commit()
        return new_unlocked_names


# ---------------------------- Дуэли ----------------------------
def has_won_today(user_id: int) -> bool:
    today = datetime.now(UTC).date()
    with SessionLocal() as session:
        count = session.scalar(
            select(func.count())
            .select_from(Duel)
            .where(
                Duel.winner_id == user_id,
                Duel.status == "completed",
                func.date(Duel.created_at) == today.isoformat(),
            )
        )
        return bool(count)


def get_available_opponents(current_user_id: int) -> list[User]:
    today = datetime.now(UTC).date().isoformat()
    with SessionLocal() as session:
        winners = select(Duel.winner_id).where(
            Duel.status == "completed", func.date(Duel.created_at) == today
        )
        active_challengers = select(Duel.challenger_id).where(Duel.status == "pending")
        active_opponents = select(Duel.opponent_id).where(Duel.status == "pending")
        users = session.scalars(
            select(User)
            .where(User.telegram_id != current_user_id)
            .where(User.telegram_id.not_in(winners))
            .where(User.telegram_id.not_in(active_challengers))
            .where(User.telegram_id.not_in(active_opponents))
        ).all()
        return list(users)


def create_duel(challenger_id: int, opponent_id: int) -> tuple[bool, str | int]:
    if challenger_id == opponent_id:
        return False, "Нельзя вызвать самого себя."
    with SessionLocal() as session:
        if has_won_today(challenger_id):
            return False, "Вы уже победили сегодня и не можете сражаться."
        if has_won_today(opponent_id):
            return False, "Ваш соперник уже победил сегодня."
        active = session.scalars(
            select(Duel).where(
                Duel.status == "pending",
                (
                    (Duel.challenger_id == challenger_id)
                    & (Duel.opponent_id == opponent_id)
                )
                | (
                    (Duel.challenger_id == opponent_id)
                    & (Duel.opponent_id == challenger_id)
                ),
            )
        ).first()
        if active:
            return False, "Между вами уже есть активный вызов."
        duel = Duel(
            challenger_id=challenger_id, opponent_id=opponent_id, status="pending"
        )
        session.add(duel)
        session.commit()
        return True, duel.id


def get_duel_by_id(duel_id: int) -> Duel | None:
    with SessionLocal() as session:
        return session.get(Duel, duel_id)


def resolve_duel(duel_id: int) -> str:
    from hearts import hearts_pool

    with SessionLocal() as session:
        duel = session.get(Duel, duel_id)
        if not duel or duel.status != "pending":
            return "Дуэль не найдена или уже завершена."
        challenger_id = duel.challenger_id
        opponent_id = duel.opponent_id
        if has_won_today(challenger_id) or has_won_today(opponent_id):
            duel.status = "cancelled"
            session.commit()
            return "Один из участников уже победил сегодня, дуэль отменена."
        heart1 = hearts_pool.get_random()
        heart2 = hearts_pool.get_random()
        duel.challenger_heart = heart1.character
        duel.opponent_heart = heart2.character
        if heart1.weight < heart2.weight:
            winner_id = challenger_id
            loser_id = opponent_id
        elif heart1.weight > heart2.weight:
            winner_id = opponent_id
            loser_id = challenger_id
        else:
            winner_id = None
            loser_id = None
        if winner_id:
            winner = session.scalars(
                select(User).where(User.telegram_id == winner_id)
            ).first()
            loser = session.scalars(
                select(User).where(User.telegram_id == loser_id)
            ).first()
            if winner:
                winner.attempts_left += 3
                winner.xp += 30
            if loser:
                loser.attempts_left = max(0, loser.attempts_left - 1)
        duel.winner_id = winner_id
        duel.status = "completed"
        session.commit()
        challenger = session.scalars(
            select(User).where(User.telegram_id == challenger_id)
        ).first()
        opponent = session.scalars(
            select(User).where(User.telegram_id == opponent_id)
        ).first()
        ch_name = challenger.full_name if challenger else str(challenger_id)
        op_name = opponent.full_name if opponent else str(opponent_id)
        msg = (
            f"⚔️ Дуэль между {ch_name} и {op_name} завершена!\n"
            f"{ch_name}: {heart1.character}\n"
            f"{op_name}: {heart2.character}\n"
        )
        if winner_id:
            msg += f"🏆 Победитель: {ch_name if winner_id == challenger_id else op_name} (+3 попытки, +30 XP)\n"
            msg += f"Проигравший: {ch_name if loser_id == challenger_id else op_name} (-1 попытка)"
        else:
            msg += "Ничья!"
        return msg


def decline_duel(duel_id: int) -> str:
    with SessionLocal() as session:
        duel = session.get(Duel, duel_id)
        if not duel or duel.status != "pending":
            return "Дуэль не найдена или уже обработана."
        duel.status = "declined"
        session.commit()
        return "Дуэль отклонена."


# ---------------------------- Лидерборды ----------------------------
def get_leaderboard_xp(limit: int = 10) -> list[tuple[User, int]]:
    with SessionLocal() as session:
        users = session.scalars(
            select(User).order_by(User.xp.desc()).limit(limit)
        ).all()
        return [(user, user.xp) for user in users]


def get_leaderboard_total_hearts(limit: int = 10) -> list[tuple[User, int]]:
    with SessionLocal() as session:
        stmt = (
            select(User, func.sum(UserHeart.count).label("total"))
            .join(UserHeart, UserHeart.user_id == User.telegram_id)
            .group_by(User.telegram_id)
            .order_by(func.sum(UserHeart.count).desc())
            .limit(limit)
        )
        result = session.execute(stmt).all()
        return [(row[0], row[1]) for row in result]


def get_leaderboard_legendary(limit: int = 10) -> list[tuple[User, int]]:
    legendary_chars = ["💝", "❣️", "❤️‍🔥"]
    with SessionLocal() as session:
        stmt = (
            select(User, func.sum(UserHeart.count).label("total"))
            .join(UserHeart, UserHeart.user_id == User.telegram_id)
            .where(UserHeart.heart_character.in_(legendary_chars))
            .group_by(User.telegram_id)
            .order_by(func.sum(UserHeart.count).desc())
            .limit(limit)
        )
        result = session.execute(stmt).all()
        return [(row[0], row[1]) for row in result]


def get_leaderboard_collection(limit: int = 10) -> list[tuple[User, int]]:
    with SessionLocal() as session:
        stmt = (
            select(User, func.count(UserHeart.heart_character).label("unique_count"))
            .join(UserHeart, UserHeart.user_id == User.telegram_id)
            .where(UserHeart.count > 0)
            .group_by(User.telegram_id)
            .order_by(func.count(UserHeart.heart_character).desc())
            .limit(limit)
        )
        result = session.execute(stmt).all()
        return [(row[0], row[1]) for row in result]


# ---------------------------- Бонусы ----------------------------
def claim_daily_bonus(telegram_id: int) -> tuple[bool, str]:
    today = datetime.now(UTC).date()
    with SessionLocal() as session:
        user = session.scalars(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if not user:
            return False, "Сначала отправьте /start"
        if user.last_daily_bonus_date == today:
            return False, "Вы уже забирали ежедневный бонус сегодня."
        if user.last_daily_bonus_date == today - timedelta(days=1):
            new_streak = user.daily_streak + 1
        else:
            new_streak = 1
        user.attempts_left += new_streak
        user.daily_streak = new_streak
        user.last_daily_bonus_date = today
        session.commit()
        return True, f"Вы получили {new_streak} попыток! Ваш стрик: {new_streak} дн."


def claim_subscription_bonus(telegram_id: int) -> tuple[bool, str]:
    with SessionLocal() as session:
        user = session.scalars(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if not user:
            return False, "Пользователь не найден. Сначала используйте /start"
        if user.bonus_claimed:
            return False, "Вы уже получали бонус за подписку!"
        user.attempts_left += 10
        user.bonus_claimed = True
        session.commit()
        return True, f"Бонус начислен! Теперь у вас {user.attempts_left} попыток."


def claim_bonus_code(telegram_id: int, code: str) -> tuple[bool, str]:
    if code.strip().upper() != "KAPACB":
        return False, "Неверный бонус-код."
    with SessionLocal() as session:
        user = session.scalars(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if not user:
            return False, "Пользователь не найден. Сначала отправьте /start."
        if user.bonus_code_claimed:
            return False, "Вы уже использовали этот бонус-код."
        user.attempts_left += 20
        user.bonus_code_claimed = True
        session.commit()
        return (
            True,
            f"Бонус-код принят! Вам начислено 20 попыток. Теперь у вас {user.attempts_left} попыток.",
        )


# ---------------------------- Реферальная система ----------------------------
def process_referral(new_user_id: int, referrer_id: int) -> tuple[bool, str]:
    if new_user_id == referrer_id:
        return False, "Нельзя пригласить самого себя."
    with SessionLocal() as session:
        new_user = session.scalars(
            select(User).where(User.telegram_id == new_user_id)
        ).first()
        if new_user:
            return False, "Вы уже зарегистрированы."
        referrer = session.scalars(
            select(User).where(User.telegram_id == referrer_id)
        ).first()
        if not referrer:
            return False, "Некорректная реферальная ссылка."
        referrer.attempts_left += 10
        session.commit()
        return True, "Бонус за приглашение начислен пригласившему."


def add_referral_bonus(telegram_id: int, referrer_id: int) -> None:
    with SessionLocal() as session:
        user = session.scalars(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if user:
            user.attempts_left += 10
            user.referred_by = referrer_id
            session.commit()


def get_referral_link(user_id: int, bot_username: str) -> str:
    return f"https://t.me/{bot_username}?start=ref_{user_id}"
