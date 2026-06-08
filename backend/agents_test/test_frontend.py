import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.frontend.agent import frontend_agent
from agents_test.fixtures import (
    SAMPLE_FRONTEND_TASKS,
    SAMPLE_PLAN,
    SAMPLE_RELEVENT_CONTEXT,
)
from state import StudioState

state = cast(
    StudioState,
    {
        "frontend_tasks": SAMPLE_FRONTEND_TASKS,
        "relevent_context": SAMPLE_RELEVENT_CONTEXT,
        "plan": SAMPLE_PLAN,
        "repository_language": "typescript",
        "repository_framework": "react",
    },
)

result = frontend_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_frontend.py
