from pydantic import BaseModel
from typing import List, Dict, Any
from schemas.implementaion import PatchRaw


class RepairRecord(BaseModel):
    issue: str
    root_cause: str
    fix: str
    verification: str


class RepairResult(BaseModel):
    records: List[RepairRecord]
    remaining_issues: List[str]
    patches: List[PatchRaw]
    integrated_state: Dict[str, Any]
    current_repair_reason: str