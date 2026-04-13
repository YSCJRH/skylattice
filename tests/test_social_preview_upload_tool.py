from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "tools" / "upload_github_social_preview.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("upload_github_social_preview", TOOL_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_social_preview_asset_matches_github_requirements() -> None:
    tool = _load_tool()
    check = tool.validate_social_preview(REPO_ROOT / "docs" / "assets" / "social-preview.png")
    assert (check.width, check.height) == (1280, 640)
    assert check.size_bytes < tool.MAX_SOCIAL_PREVIEW_BYTES


def test_repository_parser_accepts_owner_name() -> None:
    tool = _load_tool()
    assert tool.parse_repository("YSCJRH/skylattice") == "YSCJRH/skylattice"


def test_repository_parser_rejects_unsafe_values() -> None:
    tool = _load_tool()
    with pytest.raises(argparse.ArgumentTypeError):
        tool.parse_repository("https://github.com/YSCJRH/skylattice")
