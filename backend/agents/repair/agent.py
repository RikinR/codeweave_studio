from pydantic import BaseModel

from agents.common import (
    build_user_message,
    finalize_implementation_output,
    invoke_and_parse,
    merge_patch_dicts,
)
from agents.repair.model import RepairModel
from agents.repair.prompt import SYSTEM_PROMPT
from schemas.implementaion import ImplementationResult, PatchRaw
from schemas.repair import RepairResult
from state import StudioState


class RepairAgentOutput(RepairResult):
    patches: list[PatchRaw]
    integrated_state: dict
    current_repair_reason: str


def repair_agent(state: StudioState):
    model = RepairModel()
    user_message = build_user_message(
        review_issues=state.get("review_issues"),
        skeptic_findings=state.get("skeptic_findings"),
        test_results=state.get("test_results"),
        integrated_state=state.get("integrated_state"),
        patches=state.get("patches"),
        repair_history=state.get("repair_history"),
        current_repair_reason=state.get("current_repair_reason"),
        iteration_count=state.get("iteration_count"),
    )
    output = invoke_and_parse(model, SYSTEM_PROMPT, user_message, RepairAgentOutput)

    repair_result = ImplementationResult(
        summary=output.current_repair_reason,
        modified_files=[],
        patches=output.patches,
        risks=output.remaining_issues,
        open_questions=[],
    )
    _, repair_patches = finalize_implementation_output(repair_result)
    merged_patches = merge_patch_dicts(state.get("patches"), repair_patches)

    prior_history = state.get("repair_history") or []
    new_history = prior_history + [record.model_dump() for record in output.records]
    iteration_count = (state.get("iteration_count") or 0) + 1
    unresolved = list(output.remaining_issues)
    if len(repair_patches) < len(output.patches):
        unresolved.append("Some repair patches were rejected as invalid diffs")

    return {
        "repair_history": new_history,
        "patches": merged_patches,
        "integrated_state": output.integrated_state,
        "current_repair_reason": output.current_repair_reason,
        "iteration_count": iteration_count,
        "needs_changes": len(unresolved) > 0,
        "failure_reason": unresolved[0] if unresolved else None,
        "workflow_status": ["repair_completed"],
    }
