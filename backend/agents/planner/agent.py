from agents.common import build_user_message, invoke_and_parse
from agents.planner.model import PlannerModel
from agents.planner.prompt import SYSTEM_PROMPT
from schemas.plan import PlanOutput
from state import StudioState
from tools.codeweave_intelligence_tool import CodeweaveIntelligenceTool
import time

tool = CodeweaveIntelligenceTool()

def planner_agent(state: StudioState):
    print("\nPLANNER AGENT\n")
    
    iteration_count = state.get("iteration_count", 0)
    is_revision = bool(state.get("review_issues"))
    
    if is_revision:
        print(f"\nREVISING PLAN (attempt {iteration_count + 1})")
        print(f"\nReview feedback: {state.get('review_plan')}")
    
    print(state.get("goals"))
    print(state.get("relevent_context"))
    print(tool.find_related_files())
    print(tool.get_repository_map())
    
    model = PlannerModel()
    user_message = build_user_message(
        goals=state.get("goals"),
        user_request=state.get("user_request"),
        related_files=tool.find_related_files(),
        repository_map=tool.get_repository_map(),
        dependency_graph=tool.get_dependency_graph(),
        current_plan=state.get("plan"),
        review_issues=state.get("review_issues"),
        review_plan=state.get("review_plan"),
        relevent_context=state.get("relevent_context"),
        iteration_count=iteration_count,
        max_iterations=state.get("max_iterations", 5),
        decision_memory=state.get("decision_memory"),
        conversation_history=state.get("conversation_history"),
        repository_language=state.get("repository_language"),
        repository_framework=state.get("repository_framework"),
    )
    time.sleep(30)
    plan = invoke_and_parse(model, SYSTEM_PROMPT, user_message, PlanOutput, state)
    new_iteration = iteration_count + 1
    
    return {
        "plan": plan.model_dump(),
        "workflow_status": ["plan_generated"],
        "needs_changes": False,
        "iteration_count": new_iteration,
        "review_issues": [],
    }