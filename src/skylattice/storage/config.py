"""Tracked and local configuration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


JsonMapping = dict[str, Any]


def resolve_repo_root(repo_root: Path | None = None) -> Path:
    return (repo_root or Path(__file__).resolve().parents[3]).resolve()


def load_yaml(relative_path: str, repo_root: Path | None = None) -> JsonMapping:
    path = resolve_repo_root(repo_root) / relative_path
    if not path.exists():
        return {}

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Expected mapping in {path}")
    return data


def load_yaml_path(path: Path) -> JsonMapping:
    if not path.exists():
        return {}

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Expected mapping in {path}")
    return data


def deep_merge(base: JsonMapping, overlay: JsonMapping) -> JsonMapping:
    merged: JsonMapping = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
