#!/usr/bin/env python3

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.session_service import SessionService
from app.models import database, schemas

router = APIRouter()


@router.post("/upload", response_model=schemas.SessionResponse)
async def upload_subtitle(file: UploadFile = File(...), db: AsyncSession = Depends(database.get_db)):
    service = SessionService(db)

    result = await service.upload_file(file)

    return schemas.SessionResponse(
        id=result["id"],
        language=result["language"],
        filename=result["filename"],
        status=result["status"],
        styles=result["styles"],
    )


@router.post("/session/{session_id}/process", response_model=schemas.ProcessResponse)
async def process_session(
    session_id: str, request: schemas.ProcessRequest, db: AsyncSession = Depends(database.get_db)
):
    service = SessionService(db)

    await service.process_file(session_id, request.style)

    return schemas.ProcessResponse()


@router.get("/session/{session_id}/words", response_model=schemas.WordListResponse)
async def get_session_words(session_id: str, db: AsyncSession = Depends(database.get_db)):
    service = SessionService(db)

    word_items = await service.get_words(session_id)

    return schemas.WordListResponse(words=word_items, total=len(word_items))


@router.patch("/session/{session_id}/words")
async def update_session_words(
    session_id: str, request: schemas.WordUpdateRequest, db: AsyncSession = Depends(database.get_db)
):
    service = SessionService(db)

    await service.update_words(session_id, request.removed_words)

    return {"success": True, "updated": len(request.removed_words)}


@router.post("/session/{session_id}/finalize", response_model=schemas.FinalizeResponse)
async def finalize_session(session_id: str, db: AsyncSession = Depends(database.get_db)):
    service = SessionService(db)

    result = await service.finalize(session_id)

    top_words = result["top_words"]
    learned_words = result["learned_words"]
    rows = result["rows"]

    return schemas.FinalizeResponse(top_words=top_words, learned_count=len(learned_words), total_count=len(rows))
