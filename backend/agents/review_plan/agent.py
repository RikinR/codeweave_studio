import time

from agents.common import build_user_message, invoke_and_parse
from agents.review_plan.model import ReviewPlannerModel
from agents.review_plan.prompt import SYSTEM_PROMPT
from schemas.review import ReviewPlanOutput
from state import StudioState
from tools.codeweave_intelligence_tool import CodeweaveIntelligenceTool

tool = CodeweaveIntelligenceTool()

def review_planner_agent(state: StudioState):
    print("\nREVIEW PLANNER AGENT\n")
    
    iteration_count = state.get("iteration_count", 0) + 1
    is_first_review = iteration_count == 1
    
    if state.get("needs_changes") and not is_first_review:
        print("\n => Plan already reviewed and revised - skipping re-review")
        return {
            "needs_changes": False,
            "workflow_status": ["plan_approved"],
            "iteration_count": iteration_count,
        }
    
    print(state.get("plan"))
    print(state.get("relevent_context"))
    print(tool.find_related_files())
    print(tool.get_repository_map())
    
    model = ReviewPlannerModel()
    user_message = build_user_message(
        plan=state.get("plan"),
        goals=state.get("goals"),
        repository_map=tool.get_repository_map(),
        dependency_graph=tool.get_dependency_graph(),
        related_files=tool.find_related_files(),
        relevent_context=state.get("relevent_context"),
        iteration_count=iteration_count,
        is_first_review=is_first_review,
        decision_memory=state.get("decision_memory"),
        conversation_history=state.get("conversation_history"),
        review_issues=state.get("review_issues"),
        review_plan=state.get("review_plan"),
    )
    time.sleep(30)
    review = invoke_and_parse(model, SYSTEM_PROMPT, user_message, ReviewPlanOutput, state)
    
    if not is_first_review and review.issues:
        critical_issues = [i for i in review.issues if i.severity == "critical"]
        if not critical_issues:
            print("\n => Only low/medium issues remain - approving plan")
            return {
                "review_plan": review.review_plan,
                "review_issues": [issue.model_dump() for issue in review.issues],
                "needs_changes": False,
                "workflow_status": ["plan_approved"],
                "iteration_count": iteration_count,
            }
    
    return {
        "review_plan": review.review_plan,
        "review_issues": [issue.model_dump() for issue in review.issues],
        "needs_changes": not review.approved,
        "workflow_status": ["plan_approved"] if review.approved else ["plan_needs_revision"],
        "iteration_count": iteration_count,
    }