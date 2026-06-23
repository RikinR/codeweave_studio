from agents.common import build_user_message, invoke_and_parse
from agents.skeptic_review.model import SkepticReviewModel
from agents.skeptic_review.prompt import SYSTEM_PROMPT
from schemas.review import SkepticReviewOutput
from state import StudioState


def skeptic_review_agent(state: StudioState):
    model = SkepticReviewModel()
    user_message = build_user_message(
        integrated_state=state.get("integrated_state"),
        review_issues=state.get("review_issues"),
        test_results=state.get("test_results"),
        plan=state.get("plan"),
        goals=state.get("goals"),
        skeptic_findings=state.get("skeptic_findings"),
        patches=state.get("patches"),
    )
    output = invoke_and_parse(model, SYSTEM_PROMPT, user_message, SkepticReviewOutput)
    return {
        "skeptic_findings": [finding.model_dump() for finding in output.findings],
        "workflow_status": ["skeptic_review_completed"],
    }
