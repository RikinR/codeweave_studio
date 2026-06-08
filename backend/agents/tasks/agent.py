from agents.common import build_user_message, invoke_and_parse
from agents.tasks.model import TaskDividerModel
from agents.tasks.prompt import SYSTEM_PROMPT
from schemas.tasks import TaskDivisionOutput
from state import StudioState


def task_divider_agent(state: StudioState):
    model = TaskDividerModel()
    user_message = build_user_message(
        plan=state.get("plan"),
        goals=state.get("goals"),
        relevent_context=state.get("relevent_context"),
    )
    tasks = invoke_and_parse(model, SYSTEM_PROMPT, user_message, TaskDivisionOutput)
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
        "workflow_status": "tasks_divided",
    }
