from typing import Literal
from pydantic import BaseModel

class PlanStep(BaseModel):
    step_number: int
    title: str
    description: str
    affected_files: list[str]
    risk_level: Literal[
        "low",
        "medium",
        "high",
    ]
    verification_steps: list[str]

class PlanOutput(BaseModel):
    summary: str
    steps: list[PlanStep]
    risks: list[str]
    rollback_strategy: str
    completion_criteria: list[str]