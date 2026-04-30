"""Tests for ``code_context.xml_writer``."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from code_context.scanner import FileNode
from code_context.xml_writer import generate_xml, sanitize_tag


def make_tree() -> FileNode:
    root = FileNode(name="proj", rel_path="proj", is_dir=True)
    src = FileNode(name="src", rel_path="proj/src", is_dir=True)
    src.children.append(
        FileNode(
            name="main.py",
            rel_path="proj/src/main.py",
            is_dir=False,
            content="def f(a, b): return a < b & b > 0",
        )
    )
    root.children.append(src)
    root.children.append(
        FileNode(
            name="README.md",
            rel_path="proj/README.md",
            is_dir=False,
            content="# Hi",
        )
    )
    return root


def test_xml_is_well_formed():
    xml = generate_xml("proj", make_tree())
    ET.fromstring(xml)


def test_special_chars_are_escaped():
    xml = generate_xml("proj", make_tree())
    assert "&lt;" in xml
    assert "&gt;" in xml
    assert "&amp;" in xml


def test_project_name_is_escaped():
    root = FileNode(name="A&B", rel_path="A&B", is_dir=True)
    xml = generate_xml("A&B", root)
    ET.fromstring(xml)
    assert "<project_name>A&amp;B</project_name>" in xml


def test_includes_project_metadata():
    xml = generate_xml("proj", make_tree())
    parsed = ET.fromstring(xml)
    pn = parsed.find("project_context/project_name")
    ts = parsed.find("project_context/generation_timestamp")
    assert pn is not None and pn.text == "proj"
    assert ts is not None and ts.text and ts.text.endswith("UTC")


def test_structure_renders_tree_drawing():
    xml = generate_xml("proj", make_tree())
    assert "├── " in xml or "└── " in xml
    assert "proj/" in xml


def test_file_tags_use_sanitized_names():
    xml = generate_xml("proj", make_tree())
    assert "<main_py>" in xml and "</main_py>" in xml
    assert "<README_md>" in xml and "</README_md>" in xml


def test_file_content_appears_under_its_tag():
    xml = generate_xml("proj", make_tree())
    parsed = ET.fromstring(xml)
    # Walk to find <main_py> below proj/src
    proj = parsed.find("proj")
    src = proj.find("src")
    main_py = src.find("main_py")
    assert main_py is not None
    # Content includes "f(a, b)" and the escaped chars roundtrip on parse
    assert main_py.text and "f(a, b)" in main_py.text
    assert "<" in main_py.text  # escaping was reversed by parser


def test_empty_directory_has_balanced_tags():
    root = FileNode(name="empty", rel_path="empty", is_dir=True)
    xml = generate_xml("empty", root)
    parsed = ET.fromstring(xml)
    assert parsed.find("empty") is not None


@pytest.mark.parametrize(
    "name,expected",
    [
        ("valid_name", "valid_name"),
        ("invalid/name", "invalid_name"),
        ("file.txt", "file_txt"),
        ("123starts_digit", "file_123starts_digit"),
        ("", "file_"),
        ("-dash", "file__dash"),
        ("a b c", "a_b_c"),
        ("emoji_🚀", "emoji__"),
    ],
)
def test_sanitize_tag(name, expected):
    assert sanitize_tag(name) == expected
