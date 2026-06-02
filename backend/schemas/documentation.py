from pydantic import BaseModel

class DocumentationOutput(BaseModel):
    change_summary: str
    migration_notes: list[str]
    deployment_notes: list[str]
    manual_test_steps: list[str]
    breaking_changes: list[str]