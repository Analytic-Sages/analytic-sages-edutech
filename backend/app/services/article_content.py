"""Validate Insights article bodies. Authors cannot submit HTML or arbitrary embeds."""

from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException, status

ALLOWED_BLOCK_TYPES = {
    "paragraph",
    "heading",
    "list",
    "quote",
    "divider",
    "code",
    "image",
    "youtube",
    "table",
    "chart",
    "takeaways",
}

ALLOWED_CODE_LANGUAGES = {
    "sql",
    "python",
    "javascript",
    "typescript",
    "rust",
    "solidity",
    "bash",
    "json",
    "text",
}

ALLOWED_CHART_TYPES = {"line", "bar", "pie", "scatter"}
ALLOWED_IMAGE_WIDTHS = {"small", "medium", "large", "full"}
ALLOWED_IMAGE_ASPECTS = {"original", "square", "landscape", "portrait", "wide"}
YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_URL_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)
MAX_BLOCKS = 500
# Short fields (headings, captions, table cells) still use their own limits.
# A research report can be one long paragraph, so body text is much higher.
MAX_TEXT = 20000
PARAGRAPH_LIMIT = 200_000
ABSOLUTE_TEXT_LIMIT = 2_000_000
MAX_TABLE_CELLS = 2000
MAX_LIST_ITEMS = 200
MAX_TAKEAWAYS = 30


def extract_youtube_id(value: str) -> str | None:
    raw = (value or "").strip()
    if YOUTUBE_ID_RE.fullmatch(raw):
        return raw
    match = YOUTUBE_URL_RE.search(raw)
    return match.group(1) if match else None


def empty_body() -> dict[str, Any]:
    return {"version": 1, "blocks": [{"type": "paragraph", "text": ""}]}


def paragraphs_to_body(paragraphs: list[str]) -> dict[str, Any]:
    blocks = [{"type": "paragraph", "text": item.strip()} for item in paragraphs if item.strip()]
    return {"version": 1, "blocks": blocks or [{"type": "paragraph", "text": ""}]}


def reading_minutes(body: dict[str, Any]) -> int:
    words = 0
    for block in body.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        for key in ("text", "code", "caption", "title", "source", "credit"):
            value = block.get(key)
            if isinstance(value, str):
                words += len(value.split())
        for item in block.get("items") or []:
            if isinstance(item, str):
                words += len(item.split())
        for header in block.get("headers") or []:
            if isinstance(header, str):
                words += len(header.split())
        for row in block.get("rows") or []:
            if isinstance(row, list):
                for cell in row:
                    if isinstance(cell, str):
                        words += len(cell.split())
        for label in block.get("labels") or []:
            if isinstance(label, str):
                words += len(label.split())
    return max(1, round(words / 200)) if words else 1


def _clean_text(value: Any, *, limit: int = MAX_TEXT, label: str = "Text") -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text must be a string")
    text = value.replace("\x00", "").strip()
    if len(text) > limit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{label} is too long")
    lowered = text.lower()
    if "<script" in lowered or "javascript:" in lowered:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported markup")
    return text


def _split_long_text(text: str, limit: int) -> list[str]:
    """Break a report-length field into blocks instead of rejecting the article."""
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    rest = text
    while rest:
        if len(rest) <= limit:
            parts.append(rest)
            break
        window = rest[:limit]
        cut = max(window.rfind("\n\n"), window.rfind("\n"), window.rfind(". "), window.rfind(" "))
        if cut < limit // 2:
            cut = limit
        elif window[cut : cut + 2] == ". ":
            cut += 1
        chunk = rest[:cut].strip()
        rest = rest[cut:].strip()
        if chunk:
            parts.append(chunk)
    return parts


def _clean_image_src(value: Any) -> str:
    src = _clean_text(value, limit=2048, label="An image URL")
    if not src:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image URL is required")
    if src.startswith("/") and not src.startswith("//"):
        return src
    if src.startswith("https://"):
        return src
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Images must use https or a site path",
    )


def _clean_block(raw: Any) -> dict[str, Any] | list[dict[str, Any]]:
    if not isinstance(raw, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content block")
    block_type = raw.get("type")
    if block_type not in ALLOWED_BLOCK_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported content block")

    if block_type == "paragraph":
        text = _clean_text(raw.get("text"), limit=ABSOLUTE_TEXT_LIMIT, label="A paragraph")
        return [{"type": "paragraph", "text": part} for part in _split_long_text(text, PARAGRAPH_LIMIT)]
    if block_type == "heading":
        level = raw.get("level", 2)
        if level not in (1, 2, 3, 4):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Heading level must be 1-4")
        text = _clean_text(raw.get("text"), limit=5_000, label="A heading")
        if not text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Heading cannot be empty")
        return {"type": "heading", "level": level, "text": text}
    if block_type == "list":
        items = raw.get("items") or []
        if not isinstance(items, list) or not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="List needs at least one item")
        cleaned = [
            _clean_text(item, limit=PARAGRAPH_LIMIT, label="A list item") for item in items[:MAX_LIST_ITEMS]
        ]
        return {
            "type": "list",
            "ordered": bool(raw.get("ordered")),
            "items": [item for item in cleaned if item],
        }
    if block_type == "quote":
        text = _clean_text(raw.get("text"), limit=ABSOLUTE_TEXT_LIMIT, label="A quote")
        return [{"type": "quote", "text": part} for part in _split_long_text(text, PARAGRAPH_LIMIT)]
    if block_type == "divider":
        return {"type": "divider"}
    if block_type == "code":
        language = str(raw.get("language") or "text").lower().strip()
        if language not in ALLOWED_CODE_LANGUAGES:
            language = "text"
        code = raw.get("code") if isinstance(raw.get("code"), str) else ""
        code = code.replace("\x00", "")
        if len(code) > PARAGRAPH_LIMIT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code block is too long")
        return {"type": "code", "language": language, "code": code}
    if block_type == "image":
        alt = _clean_text(raw.get("alt"), limit=2_000, label="Image alt text")
        if not alt:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image alt text is required")
        width = raw.get("width") or "full"
        if width not in ALLOWED_IMAGE_WIDTHS:
            width = "full"
        aspect = raw.get("aspect") or "original"
        if aspect not in ALLOWED_IMAGE_ASPECTS:
            aspect = "original"
        return {
            "type": "image",
            "src": _clean_image_src(raw.get("src")),
            "alt": alt,
            "caption": _clean_text(raw.get("caption"), limit=5_000, label="An image caption"),
            "credit": _clean_text(raw.get("credit"), limit=1_000, label="An image credit"),
            "width": width,
            "aspect": aspect,
        }
    if block_type == "youtube":
        video_id = extract_youtube_id(str(raw.get("videoId") or raw.get("url") or ""))
        if not video_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid YouTube URL or ID")
        return {"type": "youtube", "videoId": video_id}
    if block_type == "table":
        headers = raw.get("headers") or []
        rows = raw.get("rows") or []
        if not isinstance(headers, list) or not isinstance(rows, list) or not headers:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tables need headers and rows")
        clean_headers = [_clean_text(item, limit=1_000, label="A table header") for item in headers[:12]]
        width = len(clean_headers)
        clean_rows: list[list[str]] = []
        cells = width
        for row in rows[:100]:
            if not isinstance(row, list):
                continue
            cleaned = [
                _clean_text(cell, limit=5_000, label="A table cell") for cell in (row + [""] * width)[:width]
            ]
            clean_rows.append(cleaned)
            cells += width
            if cells > MAX_TABLE_CELLS:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Table is too large")
        return {"type": "table", "headers": clean_headers, "rows": clean_rows}
    if block_type == "chart":
        chart_type = str(raw.get("chartType") or "bar").lower()
        if chart_type not in ALLOWED_CHART_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported chart type")
        labels = raw.get("labels") or []
        values = raw.get("values") or []
        if not isinstance(labels, list) or not isinstance(values, list) or len(labels) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Charts need at least two labels and matching values",
            )
        if len(labels) != len(values) or len(labels) > 80:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chart labels and values must match")
        clean_labels = [_clean_text(label, limit=500, label="A chart label") for label in labels]
        clean_values: list[float] = []
        for value in values:
            try:
                clean_values.append(float(value))
            except (TypeError, ValueError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Chart values must be numbers"
                ) from exc
        return {
            "type": "chart",
            "chartType": chart_type,
            "title": _clean_text(raw.get("title"), limit=500, label="A chart title"),
            "labels": clean_labels,
            "values": clean_values,
            "source": _clean_text(raw.get("source"), limit=2_000, label="A chart source"),
            "caption": _clean_text(raw.get("caption"), limit=2_000, label="A chart caption"),
        }
    items = raw.get("items") or []
    if not isinstance(items, list) or not items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Add at least one takeaway")
    cleaned = [
        _clean_text(item, limit=PARAGRAPH_LIMIT, label="A takeaway") for item in items[:MAX_TAKEAWAYS]
    ]
    return {"type": "takeaways", "items": [item for item in cleaned if item]}


def validate_body(raw: Any) -> dict[str, Any]:
    if raw is None:
        return empty_body()
    if not isinstance(raw, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid article body")
    blocks = raw.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Article needs at least one block")
    cleaned: list[dict[str, Any]] = []
    for block in blocks:
        result = _clean_block(block)
        if isinstance(result, list):
            cleaned.extend(result)
        else:
            cleaned.append(result)
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Article needs at least one block")
    if len(cleaned) > MAX_BLOCKS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Article has too many blocks")
    return {"version": 1, "blocks": cleaned}
