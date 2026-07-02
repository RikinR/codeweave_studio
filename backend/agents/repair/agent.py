from pydantic import BaseModel
from typing import List, Union

from agents.common import (
    build_user_message,
    finalize_implementation_output,
    invoke_and_parse,
    merge_patch_dicts,
    patches_to_dict,
    should_force_proceed,
)
from agents.repair.model import RepairModel
from agents.repair.prompt import SYSTEM_PROMPT
from schemas.implementaion import ImplementationResult, PatchRaw
from schemas.repair import RepairResult
from state import StudioState


class RepairAgentOutput(RepairResult):
    patches: List[PatchRaw]
    integrated_state: dict
    current_repair_reason: str
    remaining_issues: List[str]


def repair_agent(state: StudioState):
    print("\nREPAIR AGENT\n")
    
    repair_iteration = state.get("repair_iteration_count", 0)
    max_repair_iterations = state.get("max_repair_iterations", 2)
    
    if should_force_proceed(state):
        print(f"Max repair iterations ({max_repair_iterations}) reached. Force proceeding.")
        existing_patches = state.get("patches", [])
        if isinstance(existing_patches, dict):
            existing_patches = list(existing_patches.values())
        return {
            "repair_history": state.get("repair_history", []),
            "patches": existing_patches,
            "integrated_state": state.get("integrated_state", {}),
            "current_repair_reason": "Max iterations reached - forcing proceed",
            "iteration_count": state.get("iteration_count", 0) + 1,
            "repair_iteration_count": repair_iteration + 1,
            "needs_changes": False,
            "force_proceed": True,
            "workflow_status": ["repair_forced"],
        }
    
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
        repair_iteration_count=repair_iteration,
        max_repair_iterations=max_repair_iterations,
        decision_memory=state.get("decision_memory"),
        conversation_history=state.get("conversation_history"),
        plan=state.get("plan"),
        goals=state.get("goals"),
    )
    output = invoke_and_parse(model, SYSTEM_PROMPT, user_message, RepairAgentOutput, state)

    repair_result = ImplementationResult(
        summary=output.current_repair_reason,
        modified_files=[],
        patches=output.patches,
        risks=output.remaining_issues,
        open_questions=[],
    )
    _, repair_patches = finalize_implementation_output(repair_result)
    
    existing_patches = state.get("patches", [])
    if isinstance(existing_patches, dict):
        existing_patches = list(existing_patches.values())
    existing_patches_dict = patches_to_dict(existing_patches)
    repair_patches_dict = patches_to_dict(repair_patches)
    
    merged_dict = merge_patch_dicts(existing_patches_dict, repair_patches_dict)
    merged_list = list(merged_dict.values())

    prior_history = state.get("repair_history") or []
    new_history = prior_history + [record.model_dump() for record in output.records]
    new_repair_iteration = repair_iteration + 1
    unresolved = list(output.remaining_issues)
    if len(repair_patches) < len(output.patches):
        unresolved.append("Some repair patches were rejected as invalid diffs")
    
    should_force = new_repair_iteration >= max_repair_iterations
    needs_changes = len(unresolved) > 0 and not should_force

    return {
        "repair_history": new_history,
        "patches": merged_list,
        "integrated_state": output.integrated_state,
        "current_repair_reason": output.current_repair_reason,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "repair_iteration_count": new_repair_iteration,
        "needs_changes": needs_changes,
        "force_proceed": should_force,
        "failure_reason": unresolved[0] if unresolved and not should_force else None,
        "workflow_status": ["repair_completed"] if not needs_changes else ["repair_needed"],
    }