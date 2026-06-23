from agents.common import (
    build_user_message,
    finalize_implementation_output,
    invoke_and_parse,
    merge_patch_dicts,
)
from agents.productionise.model import ProductioniseModel
from agents.productionise.prompt import SYSTEM_PROMPT
from schemas.implementaion import ImplementationResult, ProductionChangesOutput
from state import StudioState


def productionise_agent(state: StudioState):
    model = ProductioniseModel()
    user_message = build_user_message(
        integrated_state=state.get("integrated_state"),
        patches=state.get("patches"),
        test_results=state.get("test_results"),
        plan=state.get("plan"),
    )
    result = invoke_and_parse(model, SYSTEM_PROMPT, user_message, ProductionChangesOutput)

    polish_result = ImplementationResult(
        summary=result.summary,
        modified_files=[],
        patches=result.patches,
        risks=[],
        open_questions=[],
    )
    _, polish_patches = finalize_implementation_output(polish_result)

    return {
        "production_changes": {
            "summary": result.summary,
            "changes": [change.model_dump() for change in result.changes],
        },
        "patches": merge_patch_dicts(state.get("patches"), polish_patches),
        "workflow_status": ["productionised"],
    }
