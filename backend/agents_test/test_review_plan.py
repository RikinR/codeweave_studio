import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.review_plan.agent import review_planner_agent
from agents_test.fixtures import SAMPLE_GOALS, SAMPLE_PLAN, SAMPLE_RELEVENT_CONTEXT
from state import StudioState

state = cast(
    StudioState,
    {
        "plan": SAMPLE_PLAN,
        "goals": SAMPLE_GOALS,
        "relevent_context": SAMPLE_RELEVENT_CONTEXT,
        "iteration_count": 0,
    },
)

result = review_planner_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_review_plan.py
