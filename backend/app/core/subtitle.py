#!/usr/bin/env python3

import io
import uuid
from pathlib import Path

import ass

from app.core.config import settings
from app.core import lang


def upload(filename: str, content):
    session_id = str(uuid.uuid4())

    filepath = settings.UPLOAD_DIR / f"{session_id}_{filename}"
    with open(filepath, "wb") as f:
        f.write(content)

    # TODO detect encoding
    try:
        content_str = content.decode("utf-8")
    except UnicodeDecodeError:
        content_str = content.decode("utf-8-sig")

    language = lang.check_language(content_str)

    styles = None
    file_ext = Path(filename).suffix.lower()
    if file_ext == ".ass":
        styles = _extract_styles_from_ass(content_str)

    return {
        "session_id": session_id,
        "language": language,
        "styles": styles,
        "filepath": filepath,
    }


def get_words_from_subtitle(subtitle_path: Path, style: str = None) -> tuple[list[str], list[str]]:
    content = _parse_subtitle(subtitle_path, style)
    print(content)

    language_processor = lang.init_language(content, subtitle_path)
    return language_processor.split_into_words()


def _parse_subtitle(subtitle_path: Path, style: str = None) -> tuple[list[str], list[str]]:
    name = subtitle_path.name.lower()

    if name.endswith(".ass"):
        return _parse_ass(subtitle_path, style)
    elif name.endswith(".srt"):
        lines = _parse_srt(subtitle_path)
        return lines
    else:
        raise ValueError(f"Unsupported subtitle format: {subtitle_path.suffix}")


def _parse_ass(subtitle_path: Path, style: str = None) -> tuple[list[str], list[str]]:
    # TODO detect encoding
    with open(subtitle_path, encoding="utf_8_sig") as f:
        doc = ass.parse(f)

    styles = _extract_styles_from_ass_doc(doc)

    if style is None:
        return [], styles

    if style not in styles:
        raise ValueError(f"Style '{style}' not found. Available styles: {styles}")

    lines = [e.text for e in doc.events if e.style == style]
    return "\n".join(lines)


def _parse_srt(subtitle_path: Path) -> list[str]:
    with open(subtitle_path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_styles_from_ass(content: str) -> list[str]:
    with io.StringIO(content) as f:
        doc = ass.parse(f)
        return _extract_styles_from_ass_doc(doc)


def _extract_styles_from_ass_doc(doc) -> list[str]:
    return [s.name for s in doc.styles]
