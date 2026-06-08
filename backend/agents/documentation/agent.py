from agents.common import build_user_message, invoke_and_parse
from agents.documentation.model import DocumentationModel
from agents.documentation.prompt import SYSTEM_PROMPT
from schemas.documentation import DocumentationOutput
from state import StudioState


def documentation_agent(state: StudioState):
    model = DocumentationModel()
    user_message = build_user_message(
        production_changes=state.get("production_changes"),
        integrated_state=state.get("integrated_state"),
        plan=state.get("plan"),
        goals=state.get("goals"),
        patches=state.get("patches"),
        test_results=state.get("test_results"),
    )
    docs = invoke_and_parse(model, SYSTEM_PROMPT, user_message, DocumentationOutput)
    return {
        "docs": docs.model_dump(),
        "workflow_status": "completed",
    }
