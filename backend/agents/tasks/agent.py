import time

from agents.common import build_user_message, invoke_and_parse
from agents.tasks.model import TaskDividerModel
from agents.tasks.prompt import SYSTEM_PROMPT
from schemas.tasks import TaskDivisionOutput
from state import StudioState


def task_divider_agent(state: StudioState):
    print("\nTASK DIVIDER AGENT \n")
    print(state.get("plan"))
    print(state.get("relevent_context"))
    model = TaskDividerModel()
    user_message = build_user_message(
        plan=state.get("plan"),
        goals=state.get("goals"),
        relevent_context=state.get("relevent_context"),
        decision_memory=state.get("decision_memory"),
    )
    time.sleep(30)
    tasks = invoke_and_parse(model, SYSTEM_PROMPT, user_message, TaskDivisionOutput, state)
    return {
        "frontend_tasks": {
            "tasks": [task.model_dump() for task in tasks.frontend_tasks],
        },
        "backend_tasks": {
            "tasks": [task.model_dump() for task in tasks.backend_tasks],
        },
        "database_tasks": {
            "tasks": [task.model_dump() for task in tasks.database_tasks],
        },
        "workflow_status": ["tasks_divided"],
    }