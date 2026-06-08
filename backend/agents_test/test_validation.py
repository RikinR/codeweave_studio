"""Offline validation tests — no API key required."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.common import (
    extract_json,
    is_placeholder_diff,
    is_valid_unified_diff,
    merge_patch_dicts,
    patch_quality_score,
    sanitize_patch_list,
)
from agents_test.fixtures import (
    SAMPLE_FRONTEND_PATCH,
    SAMPLE_PATCHES,
)


def test_extract_json_from_fence():
    raw = '```json\n{"ok": true}\n```'
    assert extract_json(raw) == {"ok": True}


def test_extract_json_embedded_object():
    raw = 'Here is output: {"ok": true} thanks'
    assert extract_json(raw) == {"ok": True}


def test_placeholder_diff_rejected():
    assert is_placeholder_diff("Not provided in input, assuming migration is fine")
    assert not is_valid_unified_diff("Not provided in input, assuming migration is fine")


def test_valid_unified_diff_accepted():
    diff = SAMPLE_PATCHES["src/api/users.py"]["diff"]
    assert is_valid_unified_diff(diff)
    assert patch_quality_score(diff) > 0


def test_merge_prefers_richer_patch():
    stub = {
        "file_path": "src/pages/Profile.tsx",
        "reason": "stub",
        "diff": "--- a/src/pages/Profile.tsx\n+++ b/src/pages/Profile.tsx\n@@ -1 +1,2 @@\n+export function Profile() { return <div /> }\n",
    }
    merged = merge_patch_dicts(
        {"src/pages/Profile.tsx": stub},
        {"src/pages/Profile.tsx": SAMPLE_FRONTEND_PATCH},
    )
    assert "display_name" in merged["src/pages/Profile.tsx"]["diff"]
    assert patch_quality_score(merged["src/pages/Profile.tsx"]["diff"]) > patch_quality_score(
        stub["diff"]
    )


def test_sanitize_patch_list_filters_invalid():
    valid, rejected = sanitize_patch_list(
        [
            SAMPLE_PATCHES["src/api/users.py"],
            {
                "file_path": "migrations/001_avatar.py",
                "reason": "bad",
                "diff": "assuming migration is correct",
            },
        ]
    )
    assert len(valid) == 1
    assert rejected == ["migrations/001_avatar.py"]


def run_all() -> None:
    tests = [
        test_extract_json_from_fence,
        test_extract_json_embedded_object,
        test_placeholder_diff_rejected,
        test_valid_unified_diff_accepted,
        test_merge_prefers_richer_patch,
        test_sanitize_patch_list_filters_invalid,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"\n{len(tests)} offline validation tests passed")


if __name__ == "__main__":
    run_all()

# Run from backend/: PYTHONPATH=. python agents_test/test_validation.py
