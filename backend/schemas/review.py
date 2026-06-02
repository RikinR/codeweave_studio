from typing import Literal
from pydantic import BaseModel

class ReviewIssue(BaseModel):
    severity: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ]
    file_path: str
    line_number: int
    description: str
    recommendation: str

class ReviewResult(BaseModel):
    approved: bool
    issues: list[ReviewIssue]