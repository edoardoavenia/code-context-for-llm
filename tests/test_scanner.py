"""Tests for ``code_context.scanner.Scanner``."""
from __future__ import annotations

import pytest

from code_context.config import Config, ExcludeConfig
from code_context.scanner import FileNode, Scanner, scan


@pytest.fixture
def cfg() -> Config:
    return Config(
        max_file_size_kb=4,  # 4096 bytes
        exclude=ExcludeConfig(
            extensions=(".png", ".pyc"),
            files=(".env",),
            directories=("__pycache__",),
            max_depth=10,
            max_files=50,
        ),
    )


def test_scan_returns_root_node(cfg, sample_project):
    root = Scanner(cfg).scan(sample_project)
    assert root.is_dir is True
    assert root.name == "proj"
    assert root.rel_path == "proj"


def test_excludes_by_extension(cfg, sample_project):
    root = Scanner(cfg).scan(sample_project)
    files = {n.name for n in root.walk() if not n.is_dir}
    assert "logo.png" not in files


def test_excludes_by_file_name(cfg, sample_project):
    root = Scanner(cfg).scan(sample_project)
    files = {n.name for n in root.walk() if not n.is_dir}
    assert ".env" not in files


def test_excludes_directory_entirely(cfg, sample_project):
    root = Scanner(cfg).scan(sample_project)
    dirs = {n.name for n in root.walk() if n.is_dir}
    assert "__pycache__" not in dirs


def test_excludes_oversized_files(cfg, sample_project):
    # big.txt is 5000 bytes, but max_file_size_kb=4 -> 4096 bytes.
    root = Scanner(cfg).scan(sample_project)
    files = {n.name for n in root.walk() if not n.is_dir}
    assert "big.txt" not in files


def test_excludes_non_utf8_files(cfg, sample_project):
    root = Scanner(cfg).scan(sample_project)
    files = {n.name for n in root.walk() if not n.is_dir}
    assert "data.bin" not in files


def test_includes_utf8_files_with_special_chars(cfg, sample_project):
    root = Scanner(cfg).scan(sample_project)
    by_name = {n.name: n for n in root.walk() if not n.is_dir}
    assert "xml.py" in by_name
    assert "&" in (by_name["xml.py"].content or "")


def test_max_depth_truncates_descent(sample_project):
    cfg = Config(exclude=ExcludeConfig(max_depth=1, max_files=50))
    root = Scanner(cfg).scan(sample_project)
    src = next(c for c in root.children if c.name == "src")
    # depth=1 means we descend once into src and stop
    assert src.children == []


def test_max_files_caps_per_branch(tmp_path):
    proj = tmp_path / "many"
    proj.mkdir()
    for i in range(10):
        (proj / f"f{i}.txt").write_text(str(i), encoding="utf-8")
    cfg = Config(exclude=ExcludeConfig(max_depth=5, max_files=3))
    root = Scanner(cfg).scan(proj)
    files = [n for n in root.children if not n.is_dir]
    assert len(files) == 3


def test_scan_raises_on_non_directory(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        Scanner(Config()).scan(f)


def test_scan_raises_on_missing_path(tmp_path):
    with pytest.raises(NotADirectoryError):
        Scanner(Config()).scan(tmp_path / "missing")


def test_module_scan_helper(sample_project):
    root = scan(sample_project, Config(exclude=ExcludeConfig(max_depth=10, max_files=50)))
    assert root.name == "proj"


def test_walk_yields_root_first(cfg, sample_project):
    root = Scanner(cfg).scan(sample_project)
    nodes = list(root.walk())
    assert nodes[0] is root


def test_rel_paths_are_posix(cfg, sample_project):
    root = Scanner(cfg).scan(sample_project)
    for n in root.walk():
        assert "\\" not in n.rel_path


def test_symlink_is_skipped(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    (target / "x.txt").write_text("hi", encoding="utf-8")
    proj = tmp_path / "proj"
    proj.mkdir()
    try:
        (proj / "linked").symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not supported on this platform")
    cfg = Config(exclude=ExcludeConfig(max_depth=5, max_files=10))
    root = Scanner(cfg).scan(proj)
    assert all(c.name != "linked" for c in root.children)


def test_filenode_defaults():
    n = FileNode(name="x", rel_path="x", is_dir=True)
    assert n.children == []
    assert n.content is None
