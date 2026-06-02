from typing import Literal
from pydantic import BaseModel

class AgentTrace(BaseModel):
    agent_name: str
    action: str
    status: Literal[
        "started",
        "completed",
        "failed",
    ]
    details: str

class Metric(BaseModel):
    name: str
    value: float

class DecisionRecord(BaseModel):
    agent_name: str
    decision: str
    reasoning: str