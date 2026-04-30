"""Recursive project scanner that builds a tree of UTF-8 source files."""
from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from code_context.config import Config

logger = logging.getLogger(__name__)

# Read this many bytes first to validate UTF-8 before doing a full read.
_UTF8_PROBE_BYTES = 4096


@dataclass(slots=True)
class FileNode:
    """A node in the scanned project tree.

    Directories have ``is_dir=True`` and a list of ``children``.
    Files have ``is_dir=False`` and their decoded UTF-8 ``content``.
    """

    name: str
    rel_path: str
    is_dir: bool
    children: list[FileNode] = field(default_factory=list)
    content: str | None = None

    def walk(self) -> Iterator[FileNode]:
        """Yield this node and every descendant, depth-first."""
        yield self
        for child in self.children:
            yield from child.walk()


@dataclass(slots=True)
class Scanner:
    """Walks a project root and returns a :class:`FileNode` tree.

    A file is included iff:

    * its extension is not in ``exclude.extensions``,
    * its name is not in ``exclude.files``,
    * its size is at most ``max_file_size_kb``,
    * its content decodes as valid UTF-8.

    Directories listed in ``exclude.directories`` are skipped entirely.
    Symbolic links are skipped to avoid cyclic traversal. ``max_depth``
    caps the recursion. ``max_files`` is the maximum number of immediate
    children kept per directory branch.
    """

    config: Config

    def scan(self, root: str | Path) -> FileNode:
        root_path = Path(root).resolve()
        if not root_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {root_path}")
        return self._walk(root_path, root_path, depth=0)

    def _walk(self, path: Path, root: Path, depth: int) -> FileNode:
        node = FileNode(
            name=path.name,
            rel_path=_relpath(path, root),
            is_dir=True,
        )
        if depth >= self.config.exclude.max_depth:
            return node
        try:
            entries = sorted(
                path.iterdir(),
                key=lambda e: (e.is_file(), e.name.lower()),
            )
        except OSError as exc:
            logger.error("Cannot list %s: %s", path, exc)
            return node

        slots = self.config.exclude.max_files
        for entry in entries:
            if slots <= 0:
                break
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name in self.config.exclude.directories:
                    continue
                node.children.append(self._walk(entry, root, depth + 1))
                slots -= 1
            elif entry.is_file():
                file_node = self._scan_file(entry, root)
                if file_node is not None:
                    node.children.append(file_node)
                    slots -= 1
        return node

    def _scan_file(self, path: Path, root: Path) -> FileNode | None:
        if path.suffix in self.config.exclude.extensions:
            return None
        if path.name in self.config.exclude.files:
            return None
        try:
            size = path.stat().st_size
        except OSError as exc:
            logger.error("Cannot stat %s: %s", path, exc)
            return None
        if size > self.config.max_file_size_kb * 1024:
            return None
        content = _read_utf8(path)
        if content is None:
            return None
        return FileNode(
            name=path.name,
            rel_path=_relpath(path, root),
            is_dir=False,
            content=content,
        )


def scan(root: str | Path, config: Config | None = None) -> FileNode:
    """Convenience wrapper that builds a :class:`Scanner` and runs it."""
    return Scanner(config or Config()).scan(root)


def _read_utf8(path: Path) -> str | None:
    """Return the file's decoded content, or ``None`` if it isn't valid UTF-8."""
    try:
        with path.open("rb") as f:
            head = f.read(_UTF8_PROBE_BYTES)
            head.decode("utf-8")  # raises UnicodeDecodeError if not UTF-8
            rest = f.read()
        return (head + rest).decode("utf-8")
    except UnicodeDecodeError:
        logger.debug("Skipping non-UTF-8 file: %s", path)
        return None
    except OSError as exc:
        logger.error("Cannot read %s: %s", path, exc)
        return None


def _relpath(path: Path, root: Path) -> str:
    """Return a forward-slash path rooted at the scanned directory's name."""
    if path == root:
        return root.name
    return f"{root.name}/{path.relative_to(root).as_posix()}"
