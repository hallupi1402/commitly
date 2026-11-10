from __future__ import annotations

import pytest

from commitly.document_text import DocumentTextError, MAX_DOCUMENT_BYTES, extract_document_text


def test_extracts_utf8_markdown_with_a_bounded_result() -> None:
    assert extract_document_text("paper.md", b"# Findings\nEvidence based results.") == "# Findings\nEvidence based results."


def test_rejects_invalid_utf8_oversized_and_unsupported_documents() -> None:
    with pytest.raises(DocumentTextError, match="UTF-8"):
        extract_document_text("notes.txt", b"\xff")
    with pytest.raises(DocumentTextError, match="2 MB"):
        extract_document_text("paper.pdf", b"x" * (MAX_DOCUMENT_BYTES + 1))
    with pytest.raises(DocumentTextError, match="not supported"):
        extract_document_text("image.png", b"bytes")
