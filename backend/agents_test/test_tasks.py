import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.tasks.agent import task_divider_agent
from agents_test.fixtures import SAMPLE_GOALS, SAMPLE_PLAN, SAMPLE_RELEVENT_CONTEXT
from state import StudioState

state = cast(
    StudioState,
    {
        "plan": SAMPLE_PLAN,
        "goals": SAMPLE_GOALS,
        "relevent_context": SAMPLE_RELEVENT_CONTEXT,
    },
)

result = task_divider_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_tasks.py
