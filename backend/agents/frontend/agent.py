from agents.common import (
    build_user_message,
    finalize_implementation_output,
    invoke_and_parse,
    lane_tasks_empty,
    skipped_lane_response,
)
from agents.frontend.model import FrontendModel
from agents.frontend.prompt import SYSTEM_PROMPT
from schemas.implementaion import ImplementationResult
from state import StudioState


def frontend_agent(state: StudioState):
    if lane_tasks_empty(state.get("frontend_tasks")):
        return skipped_lane_response("frontend_result", "frontend_skipped")

    model = FrontendModel()
    user_message = build_user_message(
        frontend_tasks=state.get("frontend_tasks"),
        working_context=state.get("working_context"),
        relevent_context=state.get("relevent_context"),
        plan=state.get("plan"),
        decision_memory=state.get("decision_memory"),
        backend_result=state.get("backend_result"),
        repository_language=state.get("repository_language"),
        repository_framework=state.get("repository_framework"),
    )
    result = invoke_and_parse(model, SYSTEM_PROMPT, user_message, ImplementationResult)
    frontend_result, patches = finalize_implementation_output(result)
    return {
        "frontend_result": frontend_result,
        "patches": patches,
        "workflow_status": "frontend_completed",
    }
