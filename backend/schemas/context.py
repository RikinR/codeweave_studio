from pydantic import BaseModel

class FileReference(BaseModel):
    path: str
    reason: str

class FunctionReference(BaseModel):
    name: str
    file_path: str
    reason: str

class CallChain(BaseModel):
    entry_function: str
    chain: list[str]

class ContextOutput(BaseModel):
    architecture_summary: str
    affected_files: list[FileReference]
    affected_functions: list[FunctionReference]
    call_chains: list[CallChain]
    entry_points: list[str]
    dependencies: list[str]
    retrieval_sources: list[str]
    context_gaps: list[str]