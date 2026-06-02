from pydantic import BaseModel

class RepairRecord(BaseModel):
    issue: str
    root_cause: str
    fix: str
    verification: str

class RepairResult(BaseModel):
    records: list[RepairRecord]
    remaining_issues: list[str]