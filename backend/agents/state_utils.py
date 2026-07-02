from state import StudioState
from typing import Dict, Any, Union

def validate_state(state: StudioState) -> StudioState:
    defaults = {
        "iteration_count": 0,
        "repair_iteration_count": 0,
        "max_iterations": 5,
        "max_repair_iterations": 2,
        "token_usage": 0,
        "workflow_status": [],
        "conversation_history": [],
        "decision_memory": [],
        "agent_trace": [],
        "repair_history": [],
        "needs_changes": False,
        "force_proceed": False,
        "patches": [],
        "code_files_modified_or_changed": [],
        "goals": {},
        "plan": {},
        "frontend_tasks": {},
        "backend_tasks": {},
        "database_tasks": {},
        "frontend_result": {},
        "backend_result": {},
        "database_result": {},
        "integrated_state": {},
        "integrated_patches": {},
        "review_plan": "",
        "review_issues": [],
        "tests_generated": {},
        "test_results": {},
        "production_changes": {},
        "docs": {},
        "working_context": {},
        "active_task": {},
        "current_repair_reason": "",
        "metrics": {},
        "failure_reason": None,
        "repository_id": "",
        "repository_name": "",
        "repository_language": "",
        "repository_framework": "",
        "repository_root": "",
        "current_branch": "",
        "user_request": "",
        "user_changes": {},
        "integrated_patches": {},
    }
    
    for key, default in defaults.items():
        if key not in state:
            state[key] = default
    
    return state

def cleanup_state(state: Union[StudioState, Dict[str, Any]]) -> Union[StudioState, Dict[str, Any]]:
    conversation_history = state.get("conversation_history")
    if conversation_history and len(conversation_history) > 100:
        state["conversation_history"] = conversation_history[-100:]
    
    decision_memory = state.get("decision_memory")
    if decision_memory and len(decision_memory) > 50:
        state["decision_memory"] = decision_memory[-50:]
    
    return state

def get_state_summary(state: Union[StudioState, Dict[str, Any]]) -> str:
    lines = []
    lines.append(f"Repository: {state.get('repository_name', 'Unknown')}")
    lines.append(f"Iteration: {state.get('iteration_count', 0)}")
    lines.append(f"Repair iteration: {state.get('repair_iteration_count', 0)}")
    
    workflow_status = state.get("workflow_status", [])
    lines.append(f"Status: {workflow_status[-1] if workflow_status else 'Not started'}")
    lines.append(f"Token usage: {state.get('token_usage', 0)}")
    
    test_results = state.get("test_results")
    if test_results:
        lines.append(f"Tests: {test_results.get('tests_passed', 0)} passed, {test_results.get('tests_failed', 0)} failed")
    
    plan = state.get("plan")
    if plan:
        summary = plan.get('summary', '')
        lines.append(f"Plan: {summary[:100]}..." if summary else "Plan: No summary")
    
    return "\n".join(lines)