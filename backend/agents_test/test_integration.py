import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.integration.agent import integration_agent
from agents_test.fixtures import (
    SAMPLE_BACKEND_RESULT,
    SAMPLE_DATABASE_RESULT,
    SAMPLE_FRONTEND_RESULT,
    SAMPLE_PATCHES,
    SAMPLE_PLAN,
)
from state import StudioState

state = cast(
    StudioState,
    {
        "frontend_result": SAMPLE_FRONTEND_RESULT,
        "backend_result": SAMPLE_BACKEND_RESULT,
        "database_result": SAMPLE_DATABASE_RESULT,
        "patches": SAMPLE_PATCHES,
        "plan": SAMPLE_PLAN,
        "code_files_modified_or_changed": list(SAMPLE_PATCHES.keys()),
    },
)

result = integration_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_integration.py
