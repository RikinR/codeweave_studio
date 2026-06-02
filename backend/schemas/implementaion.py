from pydantic import BaseModel

class Patch(BaseModel):
    file_path: str
    reason: str
    diff: str

class ImplementationResult(BaseModel):
    summary: str
    modified_files: list[str]
    patches: list[Patch]
    risks: list[str]
    open_questions: list[str]