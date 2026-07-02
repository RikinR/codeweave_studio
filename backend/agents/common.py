import json
import re
from typing import Any, TypeVar , Dict
from state import StudioState

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

from schemas.patch_validation import (
    is_placeholder_diff,
    is_valid_unified_diff,
    patch_quality_score,
)

EMPTY_IMPLEMENTATION_RESULT = {
    "summary": "No tasks assigned for this lane",
    "modified_files": [],
    "patches": [],
    "risks": [],
    "open_questions": [],
}

def format_state_section(title: str, data: Any) -> str | None:
    if data is None:
        return None
    if isinstance(data, (dict, list)):
        body = json.dumps(data, indent=2, default=str)
    else:
        body = str(data)
    return f"## {title}\n{body}"

def build_user_message(**sections: Any) -> str:
    parts = [
        section
        for section in (
            format_state_section(key, value) for key, value in sections.items()
        )
        if section
    ]
    if not parts:
        raise ValueError("Agent received no input context to process")
    return "\n\n".join(parts)

def lane_tasks_empty(tasks: dict | None) -> bool:
    return not tasks or not tasks.get("tasks")

def extract_json(content: str) -> Any:
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        object_match = re.search(r"\{[\s\S]*\}", text)
        if object_match:
            return json.loads(object_match.group(0))
        array_match = re.search(r"\[[\s\S]*\]", text)
        if array_match:
            return json.loads(array_match.group(0))
        raise

def invoke_and_parse(
    model: Any,
    system_prompt: str,
    user_message: str,
    output_model: type[T],
    state : StudioState
) -> T:
    response = model.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )
    print("\n\nTOKENS STATUS:")
    usage = response.usage
    print(f"Prompt Tokens: {usage.prompt_tokens}")
    print(f"Completion Tokens: {usage.completion_tokens}")
    print(f"Total Tokens: {usage.total_tokens}")
    state["token_usage"] = state.get("token_usage", 0) + usage.total_tokens
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("API returned no content")
    try:
        return output_model.model_validate(extract_json(content))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(
            f"Failed to parse {output_model.__name__} from model response: {exc}"
        ) from exc

def _patch_entry(patch: Any) -> dict:
    return patch.model_dump() if hasattr(patch, "model_dump") else dict(patch)

def patches_to_dict(patches: list[Any]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for patch in patches:
        data = _patch_entry(patch)
        file_path = data.get("file_path", "")
        if not file_path:
            continue
        existing = result.get(file_path)
        if existing is None or patch_quality_score(data["diff"]) >= patch_quality_score(
            existing["diff"]
        ):
            result[file_path] = data
    return result

def patches_from_implementation_result(result: dict | None) -> dict[str, dict]:
    if not result:
        return {}
    patches = result.get("patches", [])
    if isinstance(patches, list):
        return patches_to_dict(patches)
    return {}

def merge_patch_dicts(*patch_dicts) -> dict[str, dict]:
    merged: dict[str, dict] = {}
    for patch_dict in patch_dicts:
        if not patch_dict:
            continue
        for file_path, patch in patch_dict.items():
            if file_path not in merged:
                merged[file_path] = patch
                continue
            if patch_quality_score(patch["diff"]) > patch_quality_score(
                merged[file_path]["diff"]
            ):
                merged[file_path] = patch
    return merged

def collect_lane_patches(state: StudioState) -> dict[str, dict]:
    return merge_patch_dicts(
        patches_from_implementation_result(state.get("frontend_result")),
        patches_from_implementation_result(state.get("backend_result")),
        patches_from_implementation_result(state.get("database_result")),
        state.get("patches"),
    )

def invalid_patch_paths(patches: dict[str, dict]) -> list[str]:
    return [
        file_path
        for file_path, patch in patches.items()
        if not is_valid_unified_diff(patch.get("diff", ""))
    ]

def sanitize_patch_list(patches: list[Any]) -> tuple[list[dict], list[str]]:
    valid: list[dict] = []
    rejected: list[str] = []
    for patch in patches:
        data = _patch_entry(patch)
        file_path = data.get("file_path", "unknown")
        if is_valid_unified_diff(data.get("diff", "")):
            valid.append(data)
        else:
            rejected.append(file_path)
    return valid, rejected

def finalize_implementation_output(result: Any):
    dumped = result.model_dump()
    valid, rejected = sanitize_patch_list(dumped.get("patches", []))
    dumped["patches"] = valid
    dumped["modified_files"] = list(dict.fromkeys(p["file_path"] for p in valid))
    if rejected:
        dumped["risks"] = list(dumped.get("risks", [])) + [
            f"Rejected invalid patches for: {', '.join(rejected)}"
        ]
    return dumped, valid

def skipped_lane_response(result_key: str, workflow_status: str) -> dict:
    return {
        result_key: EMPTY_IMPLEMENTATION_RESULT,
        "patches": [],
        "workflow_status": [workflow_status],
    }

def should_force_proceed(state: StudioState, max_iterations: int = 2) -> bool:
    repair_iteration = state.get("repair_iteration_count", 0)
    if repair_iteration >= max_iterations:
        print(f"\n Max repair iterations ({max_iterations}) reached. Forcing proceed.")
        return True
    return False

def build_context_summary(state: StudioState, agent_name: str) -> str:
    parts = []
    
    goals = state.get("goals")
    if goals:
        parts.append(f"Goals: {goals.get('summary', 'Not specified')}")
    
    plan = state.get("plan")
    if plan:
        parts.append(f"Plan: {plan.get('summary', '')[:200]}...")
    
    iteration = state.get("iteration_count", 0)
    parts.append(f"Iteration: {iteration}")
    
    repair_iteration = state.get("repair_iteration_count", 0)
    if repair_iteration > 0:
        parts.append(f"Repair attempt: {repair_iteration}")
    
    test_results = state.get("test_results", {})
    if test_results:
        passed = test_results.get("tests_passed", 0)
        failed = test_results.get("tests_failed", 0)
        parts.append(f"Tests: {passed} passed, {failed} failed")
    
    return "\n".join(parts)

def get_agent_specific_context(state: StudioState, agent_name: str, memory) -> Dict:
    return {
        "history": memory.get_relevant_history(state, agent_name, limit=5),
        "decisions": memory.get_decision_memory(state, agent_name),
        "trace": memory.get_execution_trace(state, agent_name),
        "summary": build_context_summary(state, agent_name)
    }