"""Tests for ``code_context.config.load_config``."""
from __future__ import annotations

import json

import pytest

from code_context.config import Config, ExcludeConfig, load_config


def test_returns_defaults_when_file_missing(tmp_path):
    cfg = load_config(tmp_path / "missing.json")
    assert cfg == Config()


def test_returns_defaults_for_invalid_json(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    assert load_config(p) == Config()


def test_returns_defaults_when_root_is_not_object(tmp_path):
    p = tmp_path / "root.json"
    p.write_text("[]", encoding="utf-8")
    assert load_config(p) == Config()


def test_loads_full_valid_config(tmp_path):
    raw = {
        "max_file_size_kb": 50,
        "exclude": {
            "extensions": [".log", ".pyc"],
            "files": ["secret.json"],
            "directories": ["build", "dist"],
            "max_depth": 5,
            "max_files": 20,
        },
    }
    p = tmp_path / "c.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    cfg = load_config(p)
    assert cfg.max_file_size_kb == 50
    assert cfg.exclude.extensions == (".log", ".pyc")
    assert cfg.exclude.files == ("secret.json",)
    assert cfg.exclude.directories == ("build", "dist")
    assert cfg.exclude.max_depth == 5
    assert cfg.exclude.max_files == 20


def test_partial_config_keeps_defaults(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"max_file_size_kb": 7}), encoding="utf-8")
    cfg = load_config(p)
    assert cfg.max_file_size_kb == 7
    assert cfg.exclude == ExcludeConfig()


@pytest.mark.parametrize("bad", [-1, 0, 1.5, "10", True, False])
def test_max_file_size_kb_falls_back_on_invalid(tmp_path, bad):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"max_file_size_kb": bad}), encoding="utf-8")
    assert load_config(p).max_file_size_kb == Config().max_file_size_kb


def test_invalid_string_list_falls_back(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"exclude": {"extensions": "nope"}}), encoding="utf-8")
    cfg = load_config(p)
    assert cfg.exclude.extensions == ExcludeConfig().extensions


def test_zero_max_depth_falls_back(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"exclude": {"max_depth": 0}}), encoding="utf-8")
    cfg = load_config(p)
    assert cfg.exclude.max_depth == ExcludeConfig().max_depth


def test_exclude_not_object_falls_back(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"exclude": "no"}), encoding="utf-8")
    cfg = load_config(p)
    assert cfg.exclude == ExcludeConfig()
