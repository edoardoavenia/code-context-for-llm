"""Command-line interface."""
from __future__ import annotations

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from code_context.config import load_config
from code_context.inspect import char_counts, render_tree, supports_color
from code_context.scanner import Scanner
from code_context.xml_writer import generate_xml

logger = logging.getLogger("code_context")

_FILENAME_INVALID = re.compile(r"[^A-Za-z0-9\-_]")


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    # Box-drawing chars (├ └ │) need UTF-8 stdout; some shells default to cp1252.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

    args = _parse_args(argv)
    project = Path(args.path).resolve()
    if not project.is_dir():
        logger.error("Not a directory: %s", project)
        return 1

    config = load_config(args.config)
    scanner = Scanner(config)
    try:
        root = scanner.scan(project)
    except (OSError, NotADirectoryError) as exc:
        logger.error("Scan failed: %s", exc)
        return 1

    if args.inspect:
        use_colors = not args.no_color and supports_color()
        for line in render_tree(
            root,
            char_counts(root),
            directories_only=args.directories_only,
            use_colors=use_colors,
        ):
            print(line)
        return 0

    xml = generate_xml(project.name, root)
    out_path = _save_xml(xml, project.name)
    logger.info("Saved: %s", out_path)
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="code-context",
        description="Generate XML project context for LLMs.",
    )
    parser.add_argument("path", help="Project directory to scan.")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to a custom configuration file (default: bundled config.json).",
    )
    parser.add_argument(
        "-i",
        "--inspect",
        action="store_true",
        help="Show a colored tree with character counts and exit (no XML output).",
    )
    parser.add_argument(
        "-d",
        "--directories-only",
        action="store_true",
        help="With --inspect, hide files and show only directories.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output (auto-detected by default).",
    )
    return parser.parse_args(argv)


def _save_xml(xml: str, project_name: str) -> Path:
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    safe = _sanitize_filename(project_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"project_structure_{safe}_{timestamp}.txt"
    path.write_text(xml, encoding="utf-8")
    return path


def _sanitize_filename(name: str) -> str:
    sanitized = _FILENAME_INVALID.sub("_", name)
    if not sanitized or not sanitized[0].isalpha():
        sanitized = f"project_{sanitized}"
    return sanitized
