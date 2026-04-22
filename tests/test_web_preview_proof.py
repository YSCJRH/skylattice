from __future__ import annotations

from tools.check_web_preview_state import PREVIEW_STATE_PATH, load_preview_state, validate_preview_state


def test_web_preview_state_sample_is_valid() -> None:
    payload = load_preview_state()
    assert validate_preview_state(payload) == []


def test_web_preview_state_tracks_expected_representative_shapes() -> None:
    payload = load_preview_state()
    assert PREVIEW_STATE_PATH.name == "web-app-preview-state.json"
    assert any(item["online"] is True for item in payload["devices"])
    assert any(item["status"] == "pending" for item in payload["approvals"])
    assert {item["kind"] for item in payload["commands"]} >= {
        "task.run",
        "radar.scan",
        "memory.search",
    }
