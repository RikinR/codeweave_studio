import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import cast

from agents.goal.agent import goal_agent
from state import StudioState

state = cast(
    StudioState,
    {
        "user_request": "Add a user profile API endpoint with avatar URL support",
        "repository_name": "coweave_studio",
        "repository_language": "python",
        "repository_framework": "fastapi",
    },
)

result = goal_agent(state)

print(result)

# Run from backend/: PYTHONPATH=. python agents_test/test_goal.py