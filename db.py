from datetime import datetime

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

engine = create_engine("sqlite:///bot.db", echo=False)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str | None]
    full_name: Mapped[str]
    first_seen: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class StatEvent(Base):
    __tablename__ = "stat_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    event: Mapped[str]
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def add_or_update_user(telegram_id: int, username: str | None, full_name: str):
    with SessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        user = session.scalars(stmt).first()
        if user:
            user.username = username
            user.full_name = full_name
        else:
            user = User(telegram_id=telegram_id, username=username, full_name=full_name)
            session.add(user)
        session.commit()


def get_user_count() -> int:
    with SessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(User))
        return count or 0


def get_all_users():
    with SessionLocal() as session:
        return session.execute(
            select(User.telegram_id, User.username, User.full_name)
        ).all()


def log_event(telegram_id: int, event: str):
    with SessionLocal() as session:
        ev = StatEvent(user_id=telegram_id, event=event)
        session.add(ev)
        session.commit()


def get_latest_events(limit=10):
    with SessionLocal() as session:
        return (
            session.execute(
                select(StatEvent).order_by(StatEvent.timestamp.desc()).limit(limit)
            )
            .scalars()
            .all()
        )
