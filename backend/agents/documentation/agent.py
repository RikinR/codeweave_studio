import time

from agents.common import build_user_message, invoke_and_parse, patches_to_dict
from agents.documentation.model import DocumentationModel
from agents.documentation.prompt import SYSTEM_PROMPT
from schemas.documentation import DocumentationOutput
from state import StudioState


def documentation_agent(state: StudioState):
    print("\nDOCUMENTATION AGENT\n")
    model = DocumentationModel()
    patches = state.get("patches")
    if isinstance(patches, list):
        patches_context = patches_to_dict(patches)
    else:
        patches_context = patches

    user_message = build_user_message(
        production_changes=state.get("production_changes"),
        integrated_state=state.get("integrated_state"),
        plan=state.get("plan"),
        goals=state.get("goals"),
        patches=patches_context,
        test_results=state.get("test_results"),
    )
    time.sleep(30)
    docs = invoke_and_parse(model, SYSTEM_PROMPT, user_message, DocumentationOutput)
    return {
        "docs": docs.model_dump(),
        "workflow_status": ["completed"],
    }