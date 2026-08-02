from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.repository import RepositoryInfo


class FileNode(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    depth: int
    children: List["FileNode"] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class RepositoryTree(BaseModel):
    root: FileNode
    total_files: int
    total_dirs: int
    max_depth: int

    model_config = ConfigDict(frozen=True)


class TechCategory(str, Enum):
    LANGUAGE = "LANGUAGE"
    FRAMEWORK = "FRAMEWORK"
    DATABASE = "DATABASE"
    PACKAGE_MANAGER = "PACKAGE_MANAGER"
    TESTING = "TESTING"
    CONTAINER = "CONTAINER"
    CI_CD = "CI_CD"


class TechStackItem(BaseModel):
    name: str
    category: TechCategory
    confidence: float
    evidence_files: List[str]

    model_config = ConfigDict(frozen=True)


class TechStack(BaseModel):
    items: List[TechStackItem]

    @property
    def languages(self) -> List[TechStackItem]:
        return [item for item in self.items if item.category == TechCategory.LANGUAGE]

    @property
    def frameworks(self) -> List[TechStackItem]:
        return [item for item in self.items if item.category == TechCategory.FRAMEWORK]

    @property
    def databases(self) -> List[TechStackItem]:
        return [item for item in self.items if item.category == TechCategory.DATABASE]

    model_config = ConfigDict(frozen=True)


class EntryPoint(BaseModel):
    file_path: str
    line_number: int
    pattern: str
    confidence: float
    description: str

    model_config = ConfigDict(frozen=True)


class APIEndpoint(BaseModel):
    method: str
    path: str
    handler_name: str
    file_path: str
    line_number: int
    framework: str

    model_config = ConfigDict(frozen=True)


class EnvVariable(BaseModel):
    name: str
    file_path: str
    line_number: int
    access_method: str
    default_value: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class DependencyEdge(BaseModel):
    source_file: str
    target_file: str
    import_name: str

    model_config = ConfigDict(frozen=True)


class DependencyGraphModel(BaseModel):
    nodes: List[str]
    edges: List[DependencyEdge]
    connected_components: int
    most_connected: List[str]

    model_config = ConfigDict(frozen=True)


class SymbolKind(str, Enum):
    FUNCTION = "FUNCTION"
    CLASS = "CLASS"
    METHOD = "METHOD"
    MODULE = "MODULE"


class Symbol(BaseModel):
    name: str
    kind: SymbolKind
    file_path: str
    line_number: int
    parent_class: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class SymbolIndex(BaseModel):
    symbols: List[Symbol]

    def lookup(self, name: str) -> List[Symbol]:
        return [sym for sym in self.symbols if sym.name == name]

    model_config = ConfigDict(frozen=True)


class RepositoryStatistics(BaseModel):
    total_files: int
    total_dirs: int
    total_source_files: int
    languages_breakdown: Dict[str, int]
    largest_dirs: Dict[str, int]

    model_config = ConfigDict(frozen=True)


class AnalysisResult(BaseModel):
    repository_info: RepositoryInfo
    tree: RepositoryTree
    tech_stack: TechStack
    entry_points: List[EntryPoint]
    api_endpoints: List[APIEndpoint]
    env_variables: List[EnvVariable]
    dependency_graph: DependencyGraphModel
    symbol_index: SymbolIndex
    statistics: RepositoryStatistics
    analysed_at: datetime
    duration_seconds: float

    model_config = ConfigDict(frozen=True)
