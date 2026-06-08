import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.repair.agent import repair_agent
from agents_test.fixtures import (
    SAMPLE_INTEGRATED_STATE,
    SAMPLE_PATCHES,
    SAMPLE_REVIEW_ISSUES,
    SAMPLE_SKEPTIC_FINDINGS,
    SAMPLE_TEST_RESULTS,
)
from state import StudioState

state = cast(
    StudioState,
    {
        "review_issues": SAMPLE_REVIEW_ISSUES,
        "skeptic_findings": SAMPLE_SKEPTIC_FINDINGS,
        "test_results": {
            **SAMPLE_TEST_RESULTS,
            "tests_failed": 1,
            "failures": [
                {
                    "file_path": "tests/api/test_users.py",
                    "test_name": "test_profile_requires_auth",
                    "error_message": "AssertionError: expected 401 got 200",
                }
            ],
        },
        "integrated_state": SAMPLE_INTEGRATED_STATE,
        "patches": SAMPLE_PATCHES,
        "repair_history": [],
        "current_repair_reason": "Missing auth on profile endpoint",
        "iteration_count": 0,
    },
)

result = repair_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_repair.py
