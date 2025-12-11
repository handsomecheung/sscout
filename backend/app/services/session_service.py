#!/usr/bin/env python3

from typing import Set, List, Optional
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile

from app.models.database import UserWord, Word
from app.core.config import settings
from app.core import subtitle
from app.models import database, schemas


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_file(self, file: UploadFile) -> Optional[Word]:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {settings.ALLOWED_EXTENSIONS}")

        content = await file.read()

        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400, detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )

        uinfo = subtitle.upload(file.filename, content)
        session_id = uinfo["session_id"]
        language = uinfo["language"]
        styles = uinfo["styles"]
        filepath = uinfo["filepath"]

        new_session = database.Session(
            id=session_id,
            language=language,
            subtitle_filename=file.filename,
            subtitle_path=str(filepath),
            status="uploaded",
        )

        self.db.add(new_session)
        await self.db.commit()

        return {
            "id": session_id,
            "language": language,
            "filename": file.filename,
            "status": "uploaded",
            "styles": styles,
        }

    async def process_file(self, session_id: str, style: str) -> Optional[Word]:
        result = await self.db.execute(select(database.Session).where(database.Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        subtitle_path = Path(session.subtitle_path)
        current_words = subtitle.get_words_from_subtitle(subtitle_path, style)
        unknown_words = await self._filter_known_words(current_words)

        for idx, word in enumerate(unknown_words):
            frequency = current_words.count(word)

            result = await self.db.execute(select(database.Word).where(database.Word.word == word))
            word_obj = result.scalar_one_or_none()
            if word_obj is None:
                word_obj = database.Word(word=word)
                self.db.add(word_obj)
                await self.db.flush()

            session_word = database.SessionWord(
                session_id=session_id, word_id=word_obj.id, frequency=frequency, is_removed=False
            )
            self.db.add(session_word)

        session.status = "processed"
        await self.db.commit()

        return

    async def get_words(self, session_id: str) -> Optional[Word]:
        result = await self.db.execute(select(database.Session).where(database.Session.id == session_id))
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        result = await self.db.execute(
            select(database.SessionWord, database.Word)
            .join(database.Word, database.SessionWord.word_id == database.Word.id)
            .where(database.SessionWord.session_id == session_id)
        )
        rows = result.all()

        word_items = [
            schemas.WordItem(word=word.word, frequency=session_word.frequency, is_removed=session_word.is_removed)
            for session_word, word in rows
        ]

        return word_items

    async def update_words(self, session_id: str, removed_words) -> Optional[Word]:
        result = await self.db.execute(select(database.Session).where(database.Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        result = await self.db.execute(
            select(database.SessionWord, database.Word)
            .join(database.Word, database.SessionWord.word_id == database.Word.id)
            .where(database.SessionWord.session_id == session_id)
        )
        rows = result.all()

        for session_word, word in rows:
            if word.word in removed_words:
                session_word.is_removed = True

        await self.db.commit()

        return

    async def finalize(self, session_id: str) -> Optional[Word]:
        result = await self.db.execute(select(database.Session).where(database.Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        result = await self.db.execute(
            select(database.SessionWord, database.Word)
            .join(database.Word, database.SessionWord.word_id == database.Word.id)
            .where(database.SessionWord.session_id == session_id)
        )
        rows = result.all()

        learned_words = set()
        learned_word_ids = []
        unknown_words = []

        for session_word, word in rows:
            if session_word.is_removed:
                learned_words.add(word.word)
                learned_word_ids.append(word.id)
            else:
                unknown_words.append((word.word, session_word.frequency))

        user_id = settings.DEFAULT_USER
        for word_id in learned_word_ids:
            result = await self.db.execute(
                select(database.UserWord).where(
                    database.UserWord.user_id == user_id, database.UserWord.word_id == word_id
                )
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                user_word = database.UserWord(user_id=user_id, word_id=word_id, status="learned")
                self.db.add(user_word)

        unknown_words.sort(key=lambda x: x[1], reverse=True)
        top_words = [w[0] for w in unknown_words[:20]]

        session.status = "finalized"
        await self.db.commit()

        return {
            "top_words": top_words,
            "learned_words": learned_words,
            "rows": rows,
        }

    async def _load_all_words(self) -> Set[str]:
        result = await self.db.execute(
            select(Word.word)
            .join(UserWord, UserWord.word_id == Word.id)
            .where(UserWord.user_id == settings.DEFAULT_USER, UserWord.status == "learned")
        )
        words = set(result.scalars().all())
        return words

    async def _filter_known_words(self, words: List[str]) -> List[str]:
        known = await self._load_all_words()
        unknown = []

        for word in words:
            if word not in known:
                unknown.append(word)

        return unknown
