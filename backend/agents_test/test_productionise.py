import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.productionise.agent import productionise_agent
from agents_test.fixtures import (
    SAMPLE_INTEGRATED_STATE,
    SAMPLE_PATCHES,
    SAMPLE_PLAN,
    SAMPLE_TEST_RESULTS,
)
from state import StudioState

state = cast(
    StudioState,
    {
        "integrated_state": SAMPLE_INTEGRATED_STATE,
        "patches": SAMPLE_PATCHES,
        "test_results": SAMPLE_TEST_RESULTS,
        "plan": SAMPLE_PLAN,
    },
)

result = productionise_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_productionise.py
