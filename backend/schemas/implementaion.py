from pydantic import BaseModel, field_validator


class PatchRaw(BaseModel):
    file_path: str = ""
    reason: str = ""
    diff: str = ""


class Patch(BaseModel):
    file_path: str
    reason: str
    diff: str

    @field_validator("file_path")
    @classmethod
    def file_path_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("file_path must not be blank")
        return value

class ImplementationResult(BaseModel):
    summary: str
    modified_files: list[str]
    patches: list[PatchRaw]
    risks: list[str]
    open_questions: list[str]


class IntegrationOutput(BaseModel):
    summary: str
    merged_files: list[str]
    conflict_resolutions: list[str]
    contract_validations: list[str]
    integration_blocked: bool
    failure_reason: str | None
    patches: list[PatchRaw]


class ProductionChange(BaseModel):
    file_path: str
    change_type: str
    description: str
    rationale: str


class ProductionChangesOutput(BaseModel):
    summary: str
    changes: list[ProductionChange]
    patches: list[PatchRaw]