#!/usr/bin/env python3
"""Pydantic schemas for request/response validation."""

from typing import Optional
from pydantic import BaseModel


class SessionCreate(BaseModel):
    """Schema for creating a new session."""

    filename: str
    language: str


class SessionResponse(BaseModel):
    """Schema for session response."""

    id: str
    language: str
    filename: str
    status: str
    styles: Optional[list[str]] = None  # For .ass files

    class Config:
        from_attributes = True


class WordItem(BaseModel):
    """Schema for a single word."""

    word: str
    frequency: int
    is_removed: bool = False


class WordListResponse(BaseModel):
    """Schema for word list response."""

    words: list[WordItem]
    total: int


class WordUpdateRequest(BaseModel):
    """Schema for updating word status."""

    removed_words: list[str]


class ProcessRequest(BaseModel):
    """Schema for processing subtitle."""

    style: Optional[str] = None  # For .ass files


class ProcessResponse(BaseModel):
    """Schema for process response."""

    pass


class FinalizeResponse(BaseModel):
    """Schema for finalize response."""

    top_words: list[str]
    learned_count: int
    total_count: int


class KnownWordsResponse(BaseModel):
    """Schema for known words response."""

    words: list[str]
    count: int


class UserWordItem(BaseModel):
    """Schema for a user's learned word."""

    word: str
    status: str

    class Config:
        from_attributes = True


class UserWordsResponse(BaseModel):
    """Schema for user words response."""

    words: list[UserWordItem]
    count: int
