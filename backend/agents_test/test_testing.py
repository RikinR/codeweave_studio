import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.testing.agent import testing_agent
from agents_test.fixtures import (
    SAMPLE_GOALS,
    SAMPLE_INTEGRATED_STATE,
    SAMPLE_PATCHES,
    SAMPLE_PLAN,
)
from state import StudioState

state = cast(
    StudioState,
    {
        "integrated_state": SAMPLE_INTEGRATED_STATE,
        "patches": SAMPLE_PATCHES,
        "code_files_modified_or_changed": list(SAMPLE_PATCHES.keys()),
        "plan": SAMPLE_PLAN,
        "goals": SAMPLE_GOALS,
    },
)

result = testing_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_testing.py
