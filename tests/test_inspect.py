"""Tests for ``code_context.inspect``."""
from __future__ import annotations

import io

from code_context.inspect import (
    char_counts,
    format_count,
    render_tree,
    supports_color,
)
from code_context.scanner import FileNode


def make_tree() -> FileNode:
    root = FileNode(name="proj", rel_path="proj", is_dir=True)
    sub = FileNode(name="sub", rel_path="proj/sub", is_dir=True)
    sub.children.append(
        FileNode(name="c.py", rel_path="proj/sub/c.py", is_dir=False, content="x" * 10)
    )
    root.children.extend(
        [
            sub,
            FileNode(name="a.py", rel_path="proj/a.py", is_dir=False, content="x" * 100),
            FileNode(name="b.py", rel_path="proj/b.py", is_dir=False, content="x" * 50),
        ]
    )
    return root


def test_format_count_uses_dot_separator():
    assert format_count(0) == "0"
    assert format_count(123) == "123"
    assert format_count(1234) == "1.234"
    assert format_count(1234567) == "1.234.567"


def test_char_counts_aggregates_directories():
    counts = char_counts(make_tree())
    assert counts["proj/a.py"] == 100
    assert counts["proj/b.py"] == 50
    assert counts["proj/sub/c.py"] == 10
    assert counts["proj/sub"] == 10
    assert counts["proj"] == 160


def test_render_tree_root_line_shows_total():
    tree = make_tree()
    lines = render_tree(tree, char_counts(tree), use_colors=False)
    assert lines[0].startswith("proj/")
    assert "(160 chars total)" in lines[0]


def test_render_tree_directories_only_hides_files():
    tree = make_tree()
    lines = render_tree(tree, char_counts(tree), directories_only=True, use_colors=False)
    joined = "\n".join(lines)
    assert "a.py" not in joined
    assert "b.py" not in joined
    assert "sub/" in joined


def test_render_tree_no_colors_emits_no_ansi():
    tree = make_tree()
    joined = "\n".join(render_tree(tree, char_counts(tree), use_colors=False))
    assert "\033[" not in joined


def test_render_tree_with_colors_emits_ansi():
    tree = make_tree()
    joined = "\n".join(render_tree(tree, char_counts(tree), use_colors=True))
    assert "\033[" in joined


def test_supports_color_no_color_env(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert supports_color(io.StringIO()) is False


def test_supports_color_non_tty(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert supports_color(io.StringIO()) is False


def test_supports_color_dumb_terminal(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "dumb")

    class FakeTty:
        def isatty(self) -> bool:
            return True

    assert supports_color(FakeTty()) is False


def test_supports_color_real_tty(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")

    class FakeTty:
        def isatty(self) -> bool:
            return True

    assert supports_color(FakeTty()) is True
