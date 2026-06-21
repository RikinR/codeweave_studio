from agents.common import build_user_message, invoke_and_parse
from agents.review_plan.model import ReviewPlannerModel
from agents.review_plan.prompt import SYSTEM_PROMPT
from schemas.review import ReviewPlanOutput
from state import StudioState
from tools.codeweave_intelligence_tool import CodeweaveIntelligenceTool

tool = CodeweaveIntelligenceTool()

def review_planner_agent(state: StudioState):
    print("\nREVIEW PLANNER AGENT\n")
    print(state.get("plan"))
    print(tool.find_related_files())
    print(tool.get_repository_map())
    model = ReviewPlannerModel()
    user_message = build_user_message(
        plan=state.get("plan"),
        goals=state.get("goals"),
        repository_map =tool.get_repository_map(),
        dependency_graph = tool.get_dependency_graph(),
        related_files = tool.find_related_files(),
        # relevent_context=state.get("relevent_context"),
        # decision_memory=state.get("decision_memory"),
        # iteration_count=state.get("iteration_count"),
    )
    review = invoke_and_parse(model, SYSTEM_PROMPT, user_message, ReviewPlanOutput)
    return {
        "review_plan": review.review_plan,
        "review_issues": [issue.model_dump() for issue in review.issues],
        "needs_changes": not review.approved,
        "workflow_status": "plan_approved" if review.approved else "plan_needs_revision",
    }
