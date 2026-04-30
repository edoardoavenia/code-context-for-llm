"""Shared fixtures for the test suite."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Create a small, predictable project tree under ``tmp_path/proj``.

    Layout::

        proj/
            README.md
            main.py
            xml.py             (UTF-8, contains <, >, &)
            data.bin           (non UTF-8)
            .env               (excluded by name in the standard test config)
            big.txt            (5000 bytes, oversized for max_file_size_kb=4)
            src/
                util.py
                __pycache__/
                    cached.pyc
            assets/
                logo.png
            empty_dir/
    """
    root = tmp_path / "proj"
    root.mkdir()
    (root / "README.md").write_text("# Sample\n", encoding="utf-8")
    (root / "main.py").write_text("def main():\n    print('hi')\n", encoding="utf-8")
    (root / "xml.py").write_text(
        "x: int = 1\nif a < b and b > 0 and c & d:\n    pass\n",
        encoding="utf-8",
    )
    (root / "data.bin").write_bytes(bytes([0xFF, 0xFE, 0x00, 0xC0]))
    (root / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (root / "big.txt").write_text("a" * 5000, encoding="utf-8")

    src = root / "src"
    src.mkdir()
    (src / "util.py").write_text("VAL = 1\n", encoding="utf-8")
    pycache = src / "__pycache__"
    pycache.mkdir()
    (pycache / "cached.pyc").write_bytes(b"\x00\x01\x02")

    assets = root / "assets"
    assets.mkdir()
    (assets / "logo.png").write_bytes(bytes([0x89, 0x50, 0x4E, 0x47]))

    (root / "empty_dir").mkdir()
    return root
