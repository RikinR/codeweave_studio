from typing import TypedDict, Annotated
from operator import add

class StudioState(TypedDict, total=False):
    repository_id: str
    repository_name: str
    repository_language: str
    repository_framework: str
    
    user_request: str
    goals : dict
    relevent_context : dict
    working_context : dict
    plan : dict
    review_plan :str
    frontend_tasks : dict
    backend_tasks : dict
    database_tasks : dict
    frontend_result : dict
    backend_result : dict
    database_result : dict
    integrated_state: dict
    tests_generated : dict
    test_results: dict
    review_issues: list
    skeptic_findings: list
    repair_history: list
    current_repair_reason: str
    production_changes: dict
    docs: dict
    iteration_count: int
    code_files_modified_or_changed : list
    user_changes: dict
    conversation_history: list
    decision_memory: list
    active_task: dict
    patches: Annotated[list, add]
    agent_trace: list
    token_usage: dict
    metrics: dict
    failure_reason: str | None
    workflow_status: Annotated[list[str], add]
    current_branch: str
    repository_root: str
    needs_changes: bool
    integrated_patches: dict[str, dict]
    iteration_count: int
    max_iterations: int
    repair_iteration_count: int
    max_repair_iterations: int
    force_proceed: bool