#!/usr/bin/env python3
"""Database models for backend."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, relationship

from app.core.config import settings

Base = declarative_base()


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String, nullable=False, unique=True, index=True)
    definition_en = Column(String, nullable=True)
    definition_jp = Column(String, nullable=True)
    definition_zh = Column(String, nullable=True)

    session_words = relationship("SessionWord", back_populates="word_entry")
    user_words = relationship("UserWord", back_populates="word_entry")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    language = Column(String, nullable=False)
    subtitle_filename = Column(String, nullable=False)
    subtitle_path = Column(String, nullable=False)
    status = Column(String, default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    words = relationship("SessionWord", back_populates="session", cascade="all, delete-orphan")


class SessionWord(Base):
    __tablename__ = "session_words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    frequency = Column(Integer, nullable=False, default=1)
    is_removed = Column(Boolean, default=False)  # User marked as "learned"

    session = relationship("Session", back_populates="words")
    word_entry = relationship("Word", back_populates="session_words")


class UserWord(Base):
    __tablename__ = "user_words"
    __table_args__ = (UniqueConstraint("user_id", "word_id", name="uix_user_word"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=True, default="default")  # For future user system
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    status = Column(String, nullable=False, default="learned")

    word_entry = relationship("Word", back_populates="user_words")


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
