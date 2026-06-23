from pydantic import BaseModel

from agents.common import build_user_message, invalid_patch_paths, invoke_and_parse
from agents.testing.model import TestingModel
from agents.testing.prompt import SYSTEM_PROMPT
from schemas.testing import TestResult, TestsGeneratedOutput
from state import StudioState


class TestingAgentOutput(BaseModel):
    tests_generated: TestsGeneratedOutput
    test_results: TestResult


def testing_agent(state: StudioState):
    integrated_state = state.get("integrated_state") or {}
    patches = state.get("patches") or {}

    if integrated_state.get("integration_blocked"):
        return {
            "tests_generated": {"tests": []},
            "test_results": {
                "build_status": "failed",
                "lint_status": "failed",
                "typecheck_status": "failed",
                "tests_passed": 0,
                "tests_failed": 1,
                "tests_skipped": 0,
                "failures": [
                    {
                        "file_path": "integration",
                        "test_name": "integration_gate",
                        "error_message": state.get("failure_reason")
                        or "Integration blocked before testing",
                    }
                ],
            },
            "needs_changes": True,
            "workflow_status": ["testing_failed"],
        }

    invalid_paths = invalid_patch_paths(patches)
    if invalid_paths:
        return {
            "tests_generated": {"tests": []},
            "test_results": {
                "build_status": "failed",
                "lint_status": "failed",
                "typecheck_status": "failed",
                "tests_passed": 0,
                "tests_failed": len(invalid_paths),
                "tests_skipped": 0,
                "failures": [
                    {
                        "file_path": path,
                        "test_name": "patch_validation",
                        "error_message": "Invalid or placeholder unified diff",
                    }
                    for path in invalid_paths
                ],
            },
            "needs_changes": True,
            "workflow_status": ["testing_failed"],
        }

    model = TestingModel()
    user_message = build_user_message(
        integrated_state=integrated_state,
        patches=patches,
        code_files_modified_or_changed=state.get("code_files_modified_or_changed"),
        plan=state.get("plan"),
        goals=state.get("goals"),
    )
    output = invoke_and_parse(model, SYSTEM_PROMPT, user_message, TestingAgentOutput)
    has_failures = (
        output.test_results.build_status == "failed"
        or output.test_results.lint_status == "failed"
        or output.test_results.typecheck_status == "failed"
        or output.test_results.tests_failed > 0
    )
    return {
        "tests_generated": output.tests_generated.model_dump(),
        "test_results": output.test_results.model_dump(),
        "needs_changes": has_failures,
        "workflow_status": ["testing_failed"] if has_failures else ["testing_passed"],
    }
