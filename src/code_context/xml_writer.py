"""Serialize a scanned project tree to a single XML document."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from code_context.scanner import FileNode

_STRUCTURE_EXPLANATION = (
    "Directory tree of the project. Includes UTF-8 encoded files that "
    "pass the configured exclusion filters (extensions, file names, "
    "size, depth, items per branch). Directories listed under "
    "exclude.directories are skipped entirely."
)
_TAG_INVALID = re.compile(r"[^A-Za-z0-9_]")


def generate_xml(project_name: str, root: FileNode) -> str:
    """Render the scanned tree as a single XML document.

    Source content is XML-escaped (``<``, ``>``, ``&``) so the output is
    always well-formed and safely re-parseable.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    out: list[str] = ['<?xml version="1.0" encoding="UTF-8"?>', "<code>"]
    out.extend(
        [
            "    <project_context>",
            f"        <project_name>{escape(project_name)}</project_name>",
            f"        <generation_timestamp>{timestamp}</generation_timestamp>",
            "    </project_context>",
            "    <structure_explanation>",
            f"        {escape(_STRUCTURE_EXPLANATION)}",
            "    </structure_explanation>",
            "    <structure>",
        ]
    )
    for line in _tree_lines(root):
        out.append(f"        {escape(line)}")
    out.append("    </structure>")
    _emit(root, out, indent=1)
    out.append("</code>")
    return "\n".join(out)


def sanitize_tag(name: str) -> str:
    """Map an arbitrary path component to a valid XML element name."""
    sanitized = _TAG_INVALID.sub("_", name)
    if not sanitized or not sanitized[0].isalpha():
        sanitized = f"file_{sanitized}"
    return sanitized


def _tree_lines(node: FileNode, prefix: str = "", *, root: bool = True) -> list[str]:
    lines: list[str] = []
    if root:
        lines.append(f"{node.name}/")
    for i, child in enumerate(node.children):
        last = i == len(node.children) - 1
        connector = "└── " if last else "├── "
        suffix = "/" if child.is_dir else ""
        lines.append(f"{prefix}{connector}{child.name}{suffix}")
        if child.is_dir and child.children:
            extension = "    " if last else "│   "
            lines.extend(_tree_lines(child, prefix + extension, root=False))
    return lines


def _emit(node: FileNode, out: list[str], indent: int) -> None:
    pad = "    " * indent
    tag = sanitize_tag(node.name)
    out.append(f"{pad}<{tag}>")
    for child in node.children:
        if child.is_dir:
            _emit(child, out, indent + 1)
        else:
            _emit_file(child, out, indent + 1)
    out.append(f"{pad}</{tag}>")


def _emit_file(node: FileNode, out: list[str], indent: int) -> None:
    pad = "    " * indent
    tag = sanitize_tag(node.name)
    out.append(f"{pad}<{tag}>")
    content = escape(node.content or "")
    for line in content.split("\n") if content else [""]:
        out.append(f"{pad}    {line}")
    out.append(f"{pad}</{tag}>")
