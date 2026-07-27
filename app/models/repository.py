from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SourceType(str, Enum):
    GITHUB = "GITHUB"
    ZIP = "ZIP"


class UserRole(str, Enum):
    BACKEND = "Backend Developer"
    FRONTEND = "Frontend Developer"
    FULL_STACK = "Full Stack Developer"
    QA = "QA Engineer"
    DEVOPS = "DevOps Engineer"


class RepositorySource(BaseModel):
    source_type: SourceType
    url: Optional[str] = None
    local_path: str
    branch: Optional[str] = None
    
    model_config = ConfigDict(frozen=True)


class RepositoryInfo(BaseModel):
    name: str
    source: RepositorySource
    root_path: str
    cloned_at: datetime
    size_bytes: int
    
    model_config = ConfigDict(frozen=True)


class UserContext(BaseModel):
    role: UserRole
    question: Optional[str] = None
    
    model_config = ConfigDict(frozen=True)
