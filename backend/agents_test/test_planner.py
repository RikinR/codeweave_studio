import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.planner.agent import planner_agent
from agents_test.fixtures import SAMPLE_GOALS, SAMPLE_RELEVENT_CONTEXT
from state import StudioState

state = cast(
    StudioState,
    {
        "goals": SAMPLE_GOALS,
        "relevent_context": SAMPLE_RELEVENT_CONTEXT,
        "repository_language": "python",
        "repository_framework": "fastapi",
    },
)

result = planner_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_planner.py
