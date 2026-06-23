from agents.common import (
    build_user_message,
    collect_lane_patches,
    invalid_patch_paths,
    invoke_and_parse,
    merge_patch_dicts,
    patches_to_dict,
    sanitize_patch_list,
)
from agents.integration.model import IntegrationModel
from agents.integration.prompt import SYSTEM_PROMPT
from schemas.implementaion import IntegrationOutput
from state import StudioState


def integration_agent(state: StudioState):
    model = IntegrationModel()
    lane_patches = collect_lane_patches(state)
    user_message = build_user_message(
        frontend_result=state.get("frontend_result"),
        backend_result=state.get("backend_result"),
        database_result=state.get("database_result"),
        patches=lane_patches,
        plan=state.get("plan"),
        code_files_modified_or_changed=state.get("code_files_modified_or_changed"),
    )
    result = invoke_and_parse(model, SYSTEM_PROMPT, user_message, IntegrationOutput)

    valid_output, rejected = sanitize_patch_list(result.patches)
    llm_patches = patches_to_dict(valid_output)
    if rejected:
        result.conflict_resolutions = list(result.conflict_resolutions) + [
            f"Rejected invalid LLM patches for: {', '.join(rejected)}"
        ]

    final_patches = merge_patch_dicts(lane_patches, llm_patches)
    invalid_paths = invalid_patch_paths(final_patches)
    integration_blocked = result.integration_blocked or bool(invalid_paths)
    failure_reason = result.failure_reason
    if invalid_paths and not failure_reason:
        failure_reason = f"Invalid or placeholder diffs for: {', '.join(invalid_paths)}"

    merged_files = list(
        dict.fromkeys(result.merged_files or list(final_patches.keys()))
    )

    return {
        "integrated_state": {
            "summary": result.summary,
            "conflict_resolutions": result.conflict_resolutions,
            "contract_validations": result.contract_validations,
            "integration_blocked": integration_blocked,
        },
        "patches": final_patches,
        "code_files_modified_or_changed": merged_files,
        "failure_reason": failure_reason,
        "workflow_status": ["integration_blocked"] if integration_blocked else ["integration_completed"],
    }
