from agents.common import (
    build_user_message,
    finalize_implementation_output,
    invoke_and_parse,
    lane_tasks_empty,
    skipped_lane_response,
)
from agents.database.model import DatabaseModel
from agents.database.prompt import SYSTEM_PROMPT
from schemas.implementaion import ImplementationResult
from state import StudioState


def database_agent(state: StudioState):
    if lane_tasks_empty(state.get("database_tasks")):
        return skipped_lane_response("database_result", "database_skipped")

    model = DatabaseModel()
    user_message = build_user_message(
        database_tasks=state.get("database_tasks"),
        working_context=state.get("working_context"),
        relevent_context=state.get("relevent_context"),
        plan=state.get("plan"),
        backend_result=state.get("backend_result"),
        repository_language=state.get("repository_language"),
    )
    result = invoke_and_parse(model, SYSTEM_PROMPT, user_message, ImplementationResult)
    database_result, patches = finalize_implementation_output(result)
    return {
        "database_result": database_result,
        "patches": patches,
        "workflow_status": "database_completed",
    }
