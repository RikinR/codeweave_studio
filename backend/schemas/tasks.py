from typing import Literal
from pydantic import BaseModel

class Task(BaseModel):
    id: str
    title: str
    description: str
    owner: Literal[
        "frontend",
        "backend",
        "database",
    ]
    dependencies: list[str]
    acceptance_criteria: list[str]
    affected_files: list[str]

class TaskDivisionOutput(BaseModel):
    frontend_tasks: list[Task]
    backend_tasks: list[Task]
    database_tasks: list[Task]