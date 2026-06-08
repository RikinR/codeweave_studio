import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.documentation.agent import documentation_agent
from agents_test.fixtures import (
    SAMPLE_GOALS,
    SAMPLE_INTEGRATED_STATE,
    SAMPLE_PATCHES,
    SAMPLE_PLAN,
    SAMPLE_PRODUCTION_CHANGES,
    SAMPLE_TEST_RESULTS,
)
from state import StudioState

state = cast(
    StudioState,
    {
        "production_changes": SAMPLE_PRODUCTION_CHANGES,
        "integrated_state": SAMPLE_INTEGRATED_STATE,
        "plan": SAMPLE_PLAN,
        "goals": SAMPLE_GOALS,
        "patches": SAMPLE_PATCHES,
        "test_results": SAMPLE_TEST_RESULTS,
    },
)

result = documentation_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_documentation.py
