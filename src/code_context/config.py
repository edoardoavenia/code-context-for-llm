"""Configuration loading and validation."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# The default config ships next to the package so the tool behaves the same
# regardless of where it is invoked from.
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.json"


@dataclass(slots=True)
class ExcludeConfig:
    """Unified exclusion rules applied during scanning."""

    extensions: tuple[str, ...] = ()
    files: tuple[str, ...] = ()
    directories: tuple[str, ...] = ()
    max_depth: int = 10
    max_files: int = 100


@dataclass(slots=True)
class Config:
    """Top-level configuration."""

    max_file_size_kb: int = 1024
    exclude: ExcludeConfig = field(default_factory=ExcludeConfig)


def load_config(path: str | Path | None = None) -> Config:
    """Load and validate configuration from a JSON file.

    Falls back to defaults (with a warning) if the file is missing,
    unreadable, or contains invalid JSON. Individual fields with the
    wrong type are reset to their default; valid fields are kept.
    """
    if path is None:
        path = DEFAULT_CONFIG_PATH
    path = Path(path)

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("Config file not found: %s. Using defaults.", path)
        return Config()
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s. Using defaults.", path, exc)
        return Config()
    except OSError as exc:
        logger.error("Cannot read %s: %s. Using defaults.", path, exc)
        return Config()

    if not isinstance(raw, dict):
        logger.error(
            "Config root must be an object; got %s. Using defaults.",
            type(raw).__name__,
        )
        return Config()

    return _validate(raw)


def _validate(raw: dict[str, Any]) -> Config:
    cfg = Config()
    cfg.max_file_size_kb = _positive_int(
        raw.get("max_file_size_kb"), cfg.max_file_size_kb, "max_file_size_kb"
    )

    excl_raw = raw.get("exclude")
    if excl_raw is None:
        return cfg
    if not isinstance(excl_raw, dict):
        logger.warning("'exclude' must be an object; using defaults.")
        return cfg

    e = cfg.exclude
    e.extensions = _str_tuple(excl_raw.get("extensions"), e.extensions, "exclude.extensions")
    e.files = _str_tuple(excl_raw.get("files"), e.files, "exclude.files")
    e.directories = _str_tuple(
        excl_raw.get("directories"), e.directories, "exclude.directories"
    )
    e.max_depth = _positive_int(excl_raw.get("max_depth"), e.max_depth, "exclude.max_depth")
    e.max_files = _positive_int(excl_raw.get("max_files"), e.max_files, "exclude.max_files")
    return cfg


def _str_tuple(value: Any, default: tuple[str, ...], name: str) -> tuple[str, ...]:
    if value is None:
        return default
    if isinstance(value, list) and all(isinstance(x, str) for x in value):
        return tuple(value)
    logger.warning("Invalid %s (%r); using default.", name, value)
    return default


def _positive_int(value: Any, default: int, name: str) -> int:
    if value is None:
        return default
    # bool is a subclass of int; reject explicitly to avoid `True == 1`.
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        logger.warning("Invalid %s (%r); using default %d.", name, value, default)
        return default
    return value
