"""Tests for ``code_context.cli.main``."""
from __future__ import annotations

import pytest

from code_context.cli import main


def test_main_writes_xml_output(tmp_path, sample_project, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main([str(sample_project), "--no-color"])
    assert rc == 0
    out_dir = tmp_path / "output"
    files = list(out_dir.glob("project_structure_proj_*.txt"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "<code>" in text
    assert "<project_name>proj</project_name>" in text


def test_main_inspect_mode_writes_no_file(tmp_path, sample_project, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rc = main([str(sample_project), "-i", "--no-color"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "proj/" in captured.out
    assert not (tmp_path / "output").exists()


def test_main_inspect_directories_only_hides_files(tmp_path, sample_project, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rc = main([str(sample_project), "-i", "-d", "--no-color"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "main.py" not in out
    assert "src/" in out


def test_main_returns_1_on_invalid_path(tmp_path):
    assert main([str(tmp_path / "does-not-exist")]) == 1


def test_main_uses_custom_config(tmp_path, sample_project, monkeypatch):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(
        '{"max_file_size_kb": 1, "exclude": {"max_depth": 2, "max_files": 5}}',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    rc = main([str(sample_project), "--config", str(cfg), "--no-color"])
    assert rc == 0


def test_main_help_exits_cleanly(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    assert "code-context" in capsys.readouterr().out
