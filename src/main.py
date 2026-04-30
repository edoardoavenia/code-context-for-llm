import argparse
from pathlib import Path
import logging
from datetime import datetime
from file_processor import FileProcessor
from xml_generator import XMLGenerator
import re
import sys
import os
from config_manager import ConfigManager

def format_number(n: int) -> str:
    """
    Formats a number with dot separators for thousands.
    Example: 1234567 -> "1.234.567"
    """
    return f"{n:,}".replace(',', '.')

def supports_color() -> bool:
    """
    Detects if the terminal supports color output.
    Respects NO_COLOR environment variable and checks if stdout is a TTY.
    """
    # Respect NO_COLOR convention (https://no-color.org/)
    if os.environ.get('NO_COLOR'):
        return False

    # Check if output is going to a terminal
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False

    # Check TERM environment variable (avoid 'dumb' terminals)
    term = os.environ.get('TERM', '')
    if term == 'dumb':
        return False

    return True

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def sanitize_project_name(project_name: str) -> str:
    sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '_', project_name)
    if not sanitized or not sanitized[0].isalpha():
        sanitized = 'project_' + sanitized
    return sanitized

def validate_path(path: str) -> Path:
    try:
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        return path_obj
    except Exception as e:
        raise ValueError(f"Invalid path: {path}")

def save_output(content: str, project_name: str) -> str:
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    safe_name = sanitize_project_name(project_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"project_structure_{safe_name}_{timestamp}.txt"

    output_path = output_dir / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return str(output_path)

def calculate_char_counts(structure, file_contents: dict) -> tuple[dict, int, int, int, int]:
    """
    Recursively calculates character counts for each node in the directory structure.
    Returns a tuple: (char_counts dict, min_file_chars, max_file_chars, min_dir_chars, max_dir_chars)
    """
    char_counts = {}
    file_char_counts = []
    dir_char_counts = []

    def _recurse(node):
        if not node.is_dir:
            # File node: get character count from content
            content = file_contents.get(node.path, '')
            char_count = len(content)
            char_counts[node.path] = char_count
            file_char_counts.append(char_count)
            return char_count
        else:
            # Directory node: sum of all children
            total = 0
            for child in node.children:
                total += _recurse(child)
            char_counts[node.path] = total
            dir_char_counts.append(total)
            return total

    _recurse(structure)

    # Calculate min/max for files and directories separately
    min_file_chars = min(file_char_counts) if file_char_counts else 0
    max_file_chars = max(file_char_counts) if file_char_counts else 0
    min_dir_chars = min(dir_char_counts) if dir_char_counts else 0
    max_dir_chars = max(dir_char_counts) if dir_char_counts else 0

    return char_counts, min_file_chars, max_file_chars, min_dir_chars, max_dir_chars

def get_color_for_size(char_count: int, min_chars: int, max_chars: int) -> str:
    """
    Returns ANSI color code based on relative size.
    Green (small) -> Yellow -> Orange -> Red (large)
    """
    if max_chars == min_chars:
        # All files same size, use green
        return '\033[32m'  # Green

    # Calculate relative position (0.0 to 1.0)
    relative_pos = (char_count - min_chars) / (max_chars - min_chars)

    if relative_pos < 0.25:
        return '\033[32m'  # Green
    elif relative_pos < 0.5:
        return '\033[93m'  # Yellow
    elif relative_pos < 0.75:
        return '\033[33m'  # Orange
    else:
        return '\033[91m'  # Red

def display_tree_with_char_counts(structure, char_counts: dict, level: int = 0, is_last: bool = True, prefix: str = "", directories_only: bool = False, min_file_chars: int = 0, max_file_chars: int = 0, min_dir_chars: int = 0, max_dir_chars: int = 0, use_colors: bool = True) -> list:
    """
    Generates tree lines with character counts for display.
    If directories_only is True, only shows directories (no files).
    Colors are applied to character counts based on relative size (if use_colors is True).
    Files are colored based on min_file_chars/max_file_chars.
    Directories are colored based on min_dir_chars/max_dir_chars.
    """
    RESET = '\033[0m' if use_colors else ''
    lines = []

    if level == 0:
        # Root node
        total_chars = char_counts.get(structure.path, 0)
        formatted_total = format_number(total_chars)
        lines.append(f"{structure.name}/ ({formatted_total} chars total)")

    if not structure.children:
        return lines

    # Filter children based on directories_only flag
    children_to_show = [child for child in structure.children if not directories_only or child.is_dir]

    if not children_to_show:
        return lines

    for i, child in enumerate(children_to_show):
        is_child_last = (i == len(children_to_show) - 1)
        connector = "└── " if is_child_last else "├── "

        char_count = char_counts.get(child.path, 0)
        formatted_count = format_number(char_count)

        if child.is_dir:
            # Directories: apply color based on directory size range
            if use_colors:
                color = get_color_for_size(char_count, min_dir_chars, max_dir_chars)
                suffix = f" ({color}{formatted_count}{RESET} chars total)"
            else:
                suffix = f" ({formatted_count} chars total)"
        else:
            # Files: apply color based on file size range
            if use_colors:
                color = get_color_for_size(char_count, min_file_chars, max_file_chars)
                suffix = f" ({color}{formatted_count}{RESET} chars)"
            else:
                suffix = f" ({formatted_count} chars)"

        lines.append(f"{prefix}{connector}{child.name}{suffix}")

        if child.is_dir and child.children:
            # Add vertical continuation for children
            new_prefix = prefix + ("    " if is_child_last else "│   ")
            child_lines = display_tree_with_char_counts(child, char_counts, level + 1, is_child_last, new_prefix, directories_only, min_file_chars, max_file_chars, min_dir_chars, max_dir_chars, use_colors)
            # Skip the root line from recursive call
            lines.extend(child_lines[1:] if level == 0 else child_lines)

    return lines

def main():
    logger = setup_logging()

    parser = argparse.ArgumentParser(
        description="Generate XML project representation for LLMs"
    )
    parser.add_argument(
        "path",
        help="Project directory path",
        type=str
    )
    parser.add_argument(
        "--config",
        help="Optional configuration file path (default: config.json)",
        type=str,
        default="config.json"
    )
    parser.add_argument(
        "-i", "--inspect",
        help="Inspect mode: display directory tree with character counts only (no XML generation)",
        action="store_true"
    )
    parser.add_argument(
        "-d", "--directories-only",
        help="Show only directories (use with -i to display only folders with character counts)",
        action="store_true"
    )
    parser.add_argument(
        "--no-color",
        help="Disable colored output (colors are auto-detected by default)",
        action="store_true"
    )

    try:
        args = parser.parse_args()
        project_path = validate_path(args.path)

        # Load configuration from the specified file or use the default config.json
        ConfigManager().reload_config(args.config)

        processor = FileProcessor()

        # Scan the directory (applies all exclusion rules)
        scan_result = processor.scan_directory(str(project_path))

        if args.inspect:
            # Inspect mode: display tree with character counts only
            mode_desc = "directories only" if args.directories_only else "tree with character counts"
            logger.info("Running in inspect mode (%s)", mode_desc)

            # Detect color support (auto-detect unless --no-color is specified)
            use_colors = not args.no_color and supports_color()
            if use_colors:
                logger.info("Color output enabled")
            else:
                logger.info("Color output disabled")

            # Build file contents dictionary
            file_contents = {file_info['path']: file_info['content'] for file_info in scan_result.files_content}

            # Calculate character counts for all nodes and get min/max for files and directories
            char_counts, min_file_chars, max_file_chars, min_dir_chars, max_dir_chars = calculate_char_counts(scan_result.structure, file_contents)

            # Generate and display tree
            tree_lines = display_tree_with_char_counts(
                scan_result.structure,
                char_counts,
                directories_only=args.directories_only,
                min_file_chars=min_file_chars,
                max_file_chars=max_file_chars,
                min_dir_chars=min_dir_chars,
                max_dir_chars=max_dir_chars,
                use_colors=use_colors
            )
            for line in tree_lines:
                print(line)

            logger.info("Inspect complete. %d files processed", len(scan_result.files_content))
        else:
            # Normal mode: generate XML output
            generator = XMLGenerator()
            xml_content = generator.generate_xml(str(project_path), scan_result)

            project_name = project_path.name
            output_file = save_output(xml_content, project_name)
            logger.info("File saved: %s", output_file)

    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
