from agents.code_review.model import CodeReviewModel
from agents.code_review.prompt import SYSTEM_PROMPT
from agents.common import build_user_message, invoke_and_parse
from schemas.review import ReviewResult
from state import StudioState

BLOCKING_SEVERITIES = ("medium", "high", "critical")


def code_review_agent(state: StudioState):
    test_results = state.get("test_results") or {}
    if test_results.get("tests_failed", 0) > 0 or test_results.get("build_status") == "failed":
        return {
            "review_issues": state.get("review_issues") or [],
            "needs_changes": True,
            "workflow_status": "review_needs_repair",
        }

    model = CodeReviewModel()
    user_message = build_user_message(
        integrated_state=state.get("integrated_state"),
        test_results=test_results,
        plan=state.get("plan"),
        goals=state.get("goals"),
        patches=state.get("patches"),
        review_issues=state.get("review_issues"),
        skeptic_findings=state.get("skeptic_findings"),
    )
    review = invoke_and_parse(model, SYSTEM_PROMPT, user_message, ReviewResult)
    blocking = any(issue.severity in BLOCKING_SEVERITIES for issue in review.issues)
    approved = review.approved and not blocking
    return {
        "review_issues": [issue.model_dump() for issue in review.issues],
        "needs_changes": not approved,
        "workflow_status": "review_approved" if approved else "review_needs_repair",
    }
