"""Inspect mode: render the scanned tree with character counts and colors."""
from __future__ import annotations

import os
import sys

from code_context.scanner import FileNode

# ANSI color codes for adaptive size shading.
_GREEN = "\033[32m"
_YELLOW = "\033[93m"
_ORANGE = "\033[33m"
_RED = "\033[91m"
_RESET = "\033[0m"


def supports_color(stream: object | None = None) -> bool:
    """Return ``True`` if ``stream`` looks like a color-capable terminal.

    Honors the ``NO_COLOR`` convention (https://no-color.org), checks
    ``isatty()``, and rejects ``TERM=dumb``.
    """
    if "NO_COLOR" in os.environ:
        return False
    s = stream if stream is not None else sys.stdout
    if not getattr(s, "isatty", lambda: False)():
        return False
    return os.environ.get("TERM", "") != "dumb"


def format_count(n: int) -> str:
    """Format an integer with dot thousands separators (e.g. 1.234.567)."""
    return f"{n:,}".replace(",", ".")


def char_counts(node: FileNode) -> dict[str, int]:
    """Return a mapping ``{rel_path: char_count}`` for the whole tree.

    For files: the length of the decoded UTF-8 content.
    For directories: the sum of all descendant file counts.
    """
    counts: dict[str, int] = {}

    def visit(n: FileNode) -> int:
        if n.is_dir:
            total = sum(visit(c) for c in n.children)
        else:
            total = len(n.content or "")
        counts[n.rel_path] = total
        return total

    visit(node)
    return counts


def render_tree(
    root: FileNode,
    counts: dict[str, int],
    *,
    directories_only: bool = False,
    use_colors: bool = True,
) -> list[str]:
    """Build the colored tree lines for inspect mode."""
    file_values = [counts[n.rel_path] for n in root.walk() if not n.is_dir]
    dir_values = [counts[n.rel_path] for n in root.walk() if n.is_dir]
    f_lo, f_hi = (min(file_values), max(file_values)) if file_values else (0, 0)
    d_lo, d_hi = (min(dir_values), max(dir_values)) if dir_values else (0, 0)

    out: list[str] = [
        f"{root.name}/ ({format_count(counts[root.rel_path])} chars total)"
    ]
    _render(root, out, "", counts, directories_only, use_colors, f_lo, f_hi, d_lo, d_hi)
    return out


def _render(
    node: FileNode,
    out: list[str],
    prefix: str,
    counts: dict[str, int],
    dirs_only: bool,
    colors: bool,
    f_lo: int,
    f_hi: int,
    d_lo: int,
    d_hi: int,
) -> None:
    children = [c for c in node.children if c.is_dir or not dirs_only]
    for i, child in enumerate(children):
        last = i == len(children) - 1
        connector = "└── " if last else "├── "
        cnt = counts[child.rel_path]
        if child.is_dir:
            label = (
                f"({_paint(format_count(cnt), _color(cnt, d_lo, d_hi), colors)} chars total)"
            )
            out.append(f"{prefix}{connector}{child.name}/ {label}")
            ext = "    " if last else "│   "
            _render(child, out, prefix + ext, counts, dirs_only, colors, f_lo, f_hi, d_lo, d_hi)
        else:
            label = f"({_paint(format_count(cnt), _color(cnt, f_lo, f_hi), colors)} chars)"
            out.append(f"{prefix}{connector}{child.name} {label}")


def _color(value: int, lo: int, hi: int) -> str:
    if hi <= lo:
        return _GREEN
    pos = (value - lo) / (hi - lo)
    if pos < 0.25:
        return _GREEN
    if pos < 0.5:
        return _YELLOW
    if pos < 0.75:
        return _ORANGE
    return _RED


def _paint(text: str, color: str, enabled: bool) -> str:
    return f"{color}{text}{_RESET}" if enabled else text
