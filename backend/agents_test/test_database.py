import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.database.agent import database_agent
from agents_test.fixtures import (
    SAMPLE_BACKEND_RESULT,
    SAMPLE_DATABASE_TASKS,
    SAMPLE_PLAN,
    SAMPLE_RELEVENT_CONTEXT,
)
from state import StudioState

state = cast(
    StudioState,
    {
        "database_tasks": SAMPLE_DATABASE_TASKS,
        "relevent_context": SAMPLE_RELEVENT_CONTEXT,
        "plan": SAMPLE_PLAN,
        "backend_result": SAMPLE_BACKEND_RESULT,
        "repository_language": "python",
    },
)

result = database_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_database.py
