import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.backend.agent import backend_agent
from agents_test.fixtures import (
    SAMPLE_BACKEND_TASKS,
    SAMPLE_PLAN,
    SAMPLE_RELEVENT_CONTEXT,
)
from state import StudioState

state = cast(
    StudioState,
    {
        "backend_tasks": SAMPLE_BACKEND_TASKS,
        "relevent_context": SAMPLE_RELEVENT_CONTEXT,
        "plan": SAMPLE_PLAN,
        "repository_language": "python",
        "repository_framework": "fastapi",
    },
)

result = backend_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_backend.py
