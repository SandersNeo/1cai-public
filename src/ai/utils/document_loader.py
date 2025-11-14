"""Utilities to extract plain text from various document formats."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - import guarded for optional dependency
    from docx import Document as DocxDocument
except ImportError:  # pragma: no cover
    DocxDocument = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from pypdf import PdfReader  # type: ignore
except ImportError:  # pragma: no cover
    PdfReader = None  # type: ignore

logger = logging.getLogger(__name__)


def read_document(path: Path, *, encoding: str = "utf-8") -> str:
    """
    Load a document and return plain text.

    Supports .txt, .md, .json, .docx, .pdf. Unknown extensions are treated as text.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding=encoding)

    if suffix == ".json":
        data = json.loads(path.read_text(encoding=encoding))
        return json.dumps(data, ensure_ascii=False, indent=2)

    if suffix == ".docx":
        return _read_docx(path)

    if suffix == ".pdf":
        return _read_pdf(path)

    # Fallback: try to read as text
    try:
        return path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        logger.warning("Failed to decode %s with %s; returning empty string", path, encoding)
        return ""


def _read_docx(path: Path) -> str:
    if DocxDocument is None:
        logger.warning("python-docx is not installed; returning empty text for %s", path)
        return ""
    document = DocxDocument(path)
    parts = []
    for paragraph in document.paragraphs:
        parts.append(paragraph.text)
    return "\n".join(parts)


def _read_pdf(path: Path) -> str:
    if PdfReader is None:
        logger.warning("pypdf is not installed; returning empty text for %s", path)
        return ""
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception as exc:  # pragma: no cover - safety net
            logger.warning("Failed to extract PDF text from %s: %s", path, exc)
    return "\n".join(parts)

