from typing import Optional
from pydantic import BaseModel
from enum import Enum

class FileSystemOperationType(Enum):
    READ = "read"
    APPEND = "append"
    WRITE = "write"
    DELETE = "delete"

class FileSystemOperation(BaseModel):
    operation: FileSystemOperationType
    reason: str
    file_path: str
    file_content: Optional[str] = None

class FileSystemOperationResult(BaseModel):
    operation: str
    file_path: str
    file_content: Optional[str] = None