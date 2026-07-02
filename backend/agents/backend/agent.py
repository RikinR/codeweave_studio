import time

from agents.backend.model import BackendModel
from agents.backend.prompt import SYSTEM_PROMPT
from agents.common import (
    build_user_message,
    finalize_implementation_output,
    invoke_and_parse,
    lane_tasks_empty,
    skipped_lane_response,
)
from schemas.implementaion import ImplementationResult
from state import StudioState
from tools.code_read_write_tool import CodeWriteTool

tool = CodeWriteTool()

def backend_agent(state: StudioState):
    print("\nBACKEND IMPLEMENTATION AGENT\n")
    print(state.get("backend_result"))
    
    if lane_tasks_empty(state.get("backend_tasks")):
        return skipped_lane_response("backend_result", "backend_skipped")

    is_repair = state.get("repair_iteration_count", 0) > 0
    
    model = BackendModel()
    user_message = build_user_message(
        backend_tasks=state.get("backend_tasks"),
        related_files=tool.read_file(),
        relevent_context=state.get("relevent_context"),
        plan=state.get("plan"),
        goals=state.get("goals"),
        decision_memory=state.get("decision_memory"),
        conversation_history=state.get("conversation_history"),
        repository_language=state.get("repository_language"),
        repository_framework=state.get("repository_framework"),
        frontend_result=state.get("frontend_result"),
        database_result=state.get("database_result"),
        test_results=state.get("test_results"),
        is_repair=is_repair,
        current_repair_reason=state.get("current_repair_reason"),
        repair_history=state.get("repair_history"),
        integrated_state=state.get("integrated_state"),
    )
    time.sleep(30)
    result = invoke_and_parse(model, SYSTEM_PROMPT, user_message, ImplementationResult, state)
    backend_result, patches = finalize_implementation_output(result)
    print("PATCHES TYPE:", type(patches))
    print("PATCHES:", patches)
    
    return {
        "backend_result": backend_result,
        "patches": patches,
        "workflow_status": ["backend_completed"],
    }