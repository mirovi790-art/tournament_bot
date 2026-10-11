from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    chips: Mapped[int] = mapped_column(Integer, default=1000)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Ban(Base):
    __tablename__ = "bans"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    banned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Tournament(Base):
    __tablename__ = "tournaments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    access_type: Mapped[str] = mapped_column(String(16))   # open / closed
    game_type: Mapped[str] = mapped_column(String(16))     # poker / wheel
    status: Mapped[str] = mapped_column(String(16), default="registration")
    creator_id: Mapped[int] = mapped_column(BigInteger)
    start_stack: Mapped[int] = mapped_column(Integer, default=1000)
    turn_time: Mapped[int] = mapped_column(Integer, default=20)
    blind_interval: Mapped[int] = mapped_column(Integer, default=5)
    prize: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Participant(Base):
    __tablename__ = "participants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"))
    user_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    chips: Mapped[int] = mapped_column(Integer, default=0)
    place: Mapped[int | None] = mapped_column(Integer, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)