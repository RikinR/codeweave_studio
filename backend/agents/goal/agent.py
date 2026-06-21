from agents.common import build_user_message, invoke_and_parse
from agents.goal.model import GoalModel
from agents.goal.prompt import SYSTEM_PROMPT
from schemas.goal import GoalOutput
from state import StudioState


def goal_agent(state: StudioState):
    print("\nGOAL AGENT\n")
    print(state.get("user_request"))
    model = GoalModel()
    user_message = build_user_message(
        user_request=state.get("user_request"),
        conversation_history=state.get("conversation_history"),
        repository_name=state.get("repository_name"),
        repository_language=state.get("repository_language"),
        repository_framework=state.get("repository_framework"),
        user_changes=state.get("user_changes"),
    )
    goal = invoke_and_parse(model, SYSTEM_PROMPT, user_message, GoalOutput)
    return {
        "goals": goal.model_dump(),
        "workflow_status": "goal_completed",
    }