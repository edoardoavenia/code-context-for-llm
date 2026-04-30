"""End-to-end pipeline tests."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from code_context.config import Config, ExcludeConfig
from code_context.scanner import scan
from code_context.xml_writer import generate_xml


@pytest.fixture
def cfg() -> Config:
    return Config(
        max_file_size_kb=4,
        exclude=ExcludeConfig(
            extensions=(".png", ".pyc", ".bin"),
            files=(".env",),
            directories=("__pycache__",),
            max_depth=10,
            max_files=50,
        ),
    )


@pytest.mark.integration
def test_scan_then_generate_yields_well_formed_xml(cfg, sample_project):
    root = scan(sample_project, cfg)
    xml = generate_xml("proj", root)
    parsed = ET.fromstring(xml)
    assert parsed.tag == "code"
    pn = parsed.find("project_context/project_name")
    assert pn is not None and pn.text == "proj"


@pytest.mark.integration
def test_excluded_paths_are_absent_from_output(cfg, sample_project):
    root = scan(sample_project, cfg)
    xml = generate_xml("proj", root)
    assert ".env" not in xml
    assert "logo.png" not in xml
    assert "cached.pyc" not in xml
    assert "data.bin" not in xml


@pytest.mark.integration
def test_xml_content_roundtrips_with_special_chars(cfg, sample_project):
    root = scan(sample_project, cfg)
    xml = generate_xml("proj", root)
    parsed = ET.fromstring(xml)
    proj = parsed.find("proj")
    assert proj is not None
    xml_py = proj.find("xml_py")
    assert xml_py is not None
    assert xml_py.text and "<" in xml_py.text and "&" in xml_py.text
