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


def backend_agent(state: StudioState):
    if lane_tasks_empty(state.get("backend_tasks")):
        return skipped_lane_response("backend_result", "backend_skipped")

    model = BackendModel()
    user_message = build_user_message(
        backend_tasks=state.get("backend_tasks"),
        working_context=state.get("working_context"),
        relevent_context=state.get("relevent_context"),
        plan=state.get("plan"),
        decision_memory=state.get("decision_memory"),
        repository_language=state.get("repository_language"),
        repository_framework=state.get("repository_framework"),
    )
    result = invoke_and_parse(model, SYSTEM_PROMPT, user_message, ImplementationResult)
    backend_result, patches = finalize_implementation_output(result)
    return {
        "backend_result": backend_result,
        "patches": patches,
        "workflow_status": "backend_completed",
    }
