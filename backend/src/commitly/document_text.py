"""Small, bounded local text extraction for changed paper/document files."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import PurePosixPath

MAX_DOCUMENT_BYTES = 2_000_000
MAX_DOCUMENT_CHARS = 20_000
TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".rst"}


class DocumentTextError(ValueError):
    pass


def extract_document_text(path: str, content: bytes) -> str:
    suffix = PurePosixPath(path).suffix.casefold()
    if len(content) > MAX_DOCUMENT_BYTES:
        raise DocumentTextError("Document exceeds the 2 MB analysis limit")
    if suffix in TEXT_SUFFIXES:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentTextError("Document is not valid UTF-8 text") from exc
    elif suffix == ".pdf":
        executable = shutil.which("pdftotext")
        if not executable:
            raise DocumentTextError("PDF text extraction is unavailable; install pdftotext")
        try:
            result = subprocess.run([executable, "-layout", "-", "-"], input=content, capture_output=True, timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DocumentTextError("PDF text extraction did not complete") from exc
        if result.returncode:
            raise DocumentTextError("PDF is malformed, encrypted, or cannot be extracted")
        try:
            text = result.stdout.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentTextError("PDF extraction returned invalid text") from exc
        if not text.strip():
            raise DocumentTextError("PDF has no extractable text")
    else:
        raise DocumentTextError("This document format is not supported for local text analysis")
    return text[:MAX_DOCUMENT_CHARS]
