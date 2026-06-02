from typing import Literal
from pydantic import BaseModel

class GoalOutput(BaseModel):
    feature_name: str
    request_type: Literal[
        "feature",
        "bugfix",
        "refactor",
        "documentation",
        "chore",
    ]
    scope: list[str]
    constraints: list[str]
    non_goals: list[str]
    assumptions: list[str]
    success_criteria: list[str]