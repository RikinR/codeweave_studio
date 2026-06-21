from agents.common import build_user_message, invoke_and_parse
from agents.planner.model import PlannerModel
from agents.planner.prompt import SYSTEM_PROMPT
from schemas.plan import PlanOutput
from state import StudioState
from tools.codeweave_intelligence_tool import CodeweaveIntelligenceTool

tool = CodeweaveIntelligenceTool()

def planner_agent(state: StudioState):
    print("\nPLANNER AGENT\n")
    print(state.get("goals"))
    print(tool.find_related_files())
    print(tool.get_repository_map())
    model = PlannerModel()
    user_message = build_user_message(
        goals=state.get("goals"),
        related_files = tool.find_related_files(),
        repository_map =tool.get_repository_map(),
        dependency_graph = tool.get_dependency_graph(),
        review_issues=state.get("review_issues"),
        review_plan=state.get("review_plan"),
        #relevent_context=state.get("relevent_context"),
        #decision_memory=state.get("decision_memory"),
        #repository_language=state.get("repository_language"),
        #repository_framework=state.get("repository_framework"),
    )
    plan = invoke_and_parse(model, SYSTEM_PROMPT, user_message, PlanOutput)
    return {
        "plan": plan.model_dump(),
        "workflow_status": "plan_generated",
    }
