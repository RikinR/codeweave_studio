from agents.common import build_user_message, invoke_and_parse
from agents.planner.model import PlannerModel
from agents.planner.prompt import SYSTEM_PROMPT
from schemas.plan import PlanOutput
from state import StudioState


def planner_agent(state: StudioState):
    model = PlannerModel()
    user_message = build_user_message(
        goals=state.get("goals"),
        relevent_context=state.get("relevent_context"),
        decision_memory=state.get("decision_memory"),
        review_plan=state.get("review_plan"),
        review_issues=state.get("review_issues"),
        repository_language=state.get("repository_language"),
        repository_framework=state.get("repository_framework"),
    )
    plan = invoke_and_parse(model, SYSTEM_PROMPT, user_message, PlanOutput)
    return {
        "plan": plan.model_dump(),
        "workflow_status": "plan_generated",
    }
