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


class ReviewPlanOutput(BaseModel):
    approved: bool
    review_plan: str
    issues: list[ReviewIssue]


class SkepticFinding(BaseModel):
    category: Literal[
        "edge_case",
        "security",
        "scalability",
        "assumption",
        "operational",
    ]
    severity: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ]
    description: str
    scenario: str
    affected_files: list[str]
    confidence: Literal[
        "low",
        "medium",
        "high",
    ]
    recommendation: str


class SkepticReviewOutput(BaseModel):
    findings: list[SkepticFinding]