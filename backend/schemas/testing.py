from typing import Literal
from pydantic import BaseModel

class TestFailure(BaseModel):
    file_path: str
    test_name: str
    error_message: str

class TestResult(BaseModel):
    build_status: Literal[
        "passed",
        "failed",
    ]
    lint_status: Literal[
        "passed",
        "failed",
    ]
    typecheck_status: Literal[
        "passed",
        "failed",
    ]
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    failures: list[TestFailure]