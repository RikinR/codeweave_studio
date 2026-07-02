from typing import TypedDict, Annotated, Optional, List, Dict, Any
from operator import add

class StudioState(TypedDict, total=False):
    repository_id: str
    repository_name: str
    repository_language: str
    repository_framework: str
    repository_root: str

    current_branch: str
    user_request: str
    user_changes: Dict[str, Any]

    goals: Dict[str, Any]
    plan: Dict[str, Any]
    working_context: Dict[str, Any] 

    frontend_tasks: Dict[str, Any]
    backend_tasks: Dict[str, Any]
    database_tasks: Dict[str, Any]

    frontend_result: Dict[str, Any]
    backend_result: Dict[str, Any]
    database_result: Dict[str, Any]

    integrated_state: Dict[str, Any]
    integrated_patches: Dict[str, Dict[str, Any]]

    review_plan: str
    review_issues: List[Dict[str, Any]]
    needs_changes: bool
    force_proceed: bool

    tests_generated: Dict[str, Any]
    test_results: Dict[str, Any]

    patches: Annotated[List[Dict[str, Any]], add]
    code_files_modified_or_changed: List[str]
    conversation_history: Annotated[List[Dict[str, Any]], add]
    decision_memory: Annotated[List[Dict[str, Any]], add]
    agent_trace: Annotated[List[Dict[str, Any]], add]
    repair_history: Annotated[List[Dict[str, Any]], add]

    iteration_count: int
    max_iterations: int
    repair_iteration_count: int
    max_repair_iterations: int

    workflow_status: Annotated[List[str], add]
    token_usage: int
    metrics: Dict[str, Any]
    failure_reason: Optional[str]
    
    active_task: Dict[str, Any]
    current_repair_reason: str
    production_changes: Dict[str, Any]
    docs: Dict[str, Any]