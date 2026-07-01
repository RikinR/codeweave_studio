from agents.common import (
    build_user_message,
    finalize_implementation_output,
    invoke_and_parse,
    patches_to_dict,
)
from agents.productionise.model import ProductioniseModel
from agents.productionise.prompt import SYSTEM_PROMPT
from schemas.implementaion import ImplementationResult, ProductionChangesOutput
from state import StudioState


def productionise_agent(state: StudioState):
    print("\nPRODUCTIONIZE AGENT\n")
    
    force_proceed = state.get("force_proceed", False)
    if force_proceed:
        print("Force proceeding with productionize despite unresolved issues")
    
    model = ProductioniseModel()
    user_message = build_user_message(
        integrated_state=state.get("integrated_state"),
        patches=state.get("patches"),
        test_results=state.get("test_results"),
        plan=state.get("plan"),
        force_proceed=force_proceed,
        repair_history=state.get("repair_history"),
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

    existing_patches = state.get("patches") or []
    if isinstance(existing_patches, dict):
        existing_patches = list(existing_patches.values())
    existing_patches_dict = patches_to_dict(existing_patches)
    polish_patches_dict = patches_to_dict(polish_patches)

    merged_dict = {**existing_patches_dict, **polish_patches_dict}
    merged_list = list(merged_dict.values())

    return {
        "production_changes": {
            "summary": result.summary,
            "changes": [change.model_dump() for change in result.changes],
        },
        "patches": merged_list,
        "workflow_status": ["productionised"],
    }