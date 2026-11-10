from __future__ import annotations

import pytest

from commitly.config import get_settings, update_settings


def test_local_analyzer_settings_persist_without_secrets(tmp_path) -> None:
    saved = update_settings({"model_path": "/models/local.gguf", "model_executable": "llama-cli"}, tmp_path, tmp_path / "workspace")
    assert saved["model_path"] == "/models/local.gguf"
    assert get_settings(tmp_path, tmp_path / "workspace")["model_executable"] == "llama-cli"
    assert (tmp_path / "settings.json").stat().st_mode & 0o777 == 0o600


def test_invalid_local_analyzer_settings_are_rejected(tmp_path) -> None:
    with pytest.raises(ValueError, match="executable"):
        update_settings({"model_executable": "\n"}, tmp_path)
