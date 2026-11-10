"""XDG paths and small user preference/backup state files."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


def _xdg(env_name: str, fallback: str) -> Path:
    return Path(os.environ.get(env_name, Path.home() / fallback)).expanduser().resolve()


def source_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_workspace() -> Path:
    return _xdg("XDG_DATA_HOME", ".local/share") / "commitly" / "journal"


def resolve_workspace(value: str | Path | None = None) -> Path:
    workspace = Path(value).expanduser().resolve() if value else default_workspace()
    try:
        workspace.relative_to(source_root())
    except ValueError:
        return workspace
    raise ValueError("Journal workspace must be outside the Commitly source checkout")


def config_dir() -> Path:
    return _xdg("XDG_CONFIG_HOME", ".config") / "commitly"


def state_dir() -> Path:
    return _xdg("XDG_STATE_HOME", ".local/state") / "commitly"


def _read(path: Path, default: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default.copy()
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Cannot read Commitly settings at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Commitly settings at {path} must contain a JSON object")
    return value


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
        dfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def get_settings(config_path: Path | None = None, workspace: Path | None = None) -> dict:
    path = config_path or config_dir()
    settings = _read(path / "settings.json", {"theme": "system"})
    theme = settings.get("theme", "system")
    if theme not in {"system", "light", "dark"}:
        raise ValueError("Theme must be system, light, or dark")
    return {"workspace_path": str(workspace or default_workspace()), "theme": theme}


def update_settings(patch: dict, config_path: Path | None = None, workspace: Path | None = None) -> dict:
    if set(patch) - {"theme"}:
        raise ValueError("Only basic preferences can be changed")
    current = get_settings(config_path, workspace)
    theme = patch.get("theme", current["theme"])
    if theme not in {"system", "light", "dark"}:
        raise ValueError("Theme must be system, light, or dark")
    _write((config_path or config_dir()) / "settings.json", {"theme": theme})
    return get_settings(config_path, workspace)


def get_backup_configuration(config_path: Path | None = None) -> dict:
    value = _read((config_path or config_dir()) / "backup.json", {"enabled": False, "remote_url": None, "branch": "main", "private_confirmed": False})
    if not isinstance(value.get("enabled"), bool) or not isinstance(value.get("private_confirmed"), bool):
        raise ValueError("Backup configuration is malformed")
    remote = value.get("remote_url")
    if value["enabled"] and (not remote or not value["private_confirmed"]):
        value["enabled"] = False
    value.setdefault("branch", "main")
    return value


def update_backup_configuration(value: dict, config_path: Path | None = None) -> dict:
    enabled = value.get("enabled")
    remote = value.get("remote_url")
    if remote is None:
        remote = get_backup_configuration(config_path).get("remote_url")
    branch = value.get("branch", "main")
    confirmed = value.get("private_confirmed")
    if not isinstance(enabled, bool) or not isinstance(confirmed, bool):
        raise ValueError("enabled and private_confirmed must be booleans")
    if enabled and (not isinstance(remote, str) or not remote.strip() or not confirmed):
        raise ValueError("A destination and privacy confirmation are required before enabling push")
    if remote is not None and not isinstance(remote, str):
        raise ValueError("remote_url must be text or null")
    if remote and "\n" in remote:
        raise ValueError("remote_url is invalid")
    if remote:
        parsed_remote = urlsplit(remote)
        if parsed_remote.password or (parsed_remote.username and parsed_remote.scheme not in {"ssh"}):
            raise ValueError("Do not put credentials in the backup URL; use the Git credential helper")
    if not isinstance(branch, str) or not branch.strip():
        raise ValueError("branch must be non-empty text")
    result = {"enabled": enabled, "remote_url": remote.strip() if remote else None, "branch": branch.strip(), "private_confirmed": confirmed}
    _write((config_path or config_dir()) / "backup.json", result)
    return result


def read_backup_status(state_path: Path | None = None) -> dict:
    return _read(state_path or state_dir() / "backup-status.json", {})


def write_backup_status(status: dict, state_path: Path | None = None) -> None:
    _write(state_path or state_dir() / "backup-status.json", status)
