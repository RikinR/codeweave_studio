import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.skeptic_review.agent import skeptic_review_agent
from agents_test.fixtures import (
    SAMPLE_GOALS,
    SAMPLE_INTEGRATED_STATE,
    SAMPLE_PATCHES,
    SAMPLE_PLAN,
    SAMPLE_REVIEW_ISSUES,
    SAMPLE_TEST_RESULTS,
)
from state import StudioState

state = cast(
    StudioState,
    {
        "integrated_state": SAMPLE_INTEGRATED_STATE,
        "review_issues": SAMPLE_REVIEW_ISSUES,
        "test_results": SAMPLE_TEST_RESULTS,
        "plan": SAMPLE_PLAN,
        "goals": SAMPLE_GOALS,
        "patches": SAMPLE_PATCHES,
        "skeptic_findings": [],
    },
)

result = skeptic_review_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_skeptic_review.py
