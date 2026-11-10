from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from commitly.app import create_app


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    return tmp_path / "journal"


@pytest.fixture
def client(workspace: Path) -> Iterator[TestClient]:
    with TestClient(create_app(workspace=workspace, config_dir=workspace / "config", state_dir=workspace / "state")) as value:
        yield value
