from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FailureBehavior(str, Enum):
    """How the job runner should classify an adapter failure."""

    RETRYABLE = "retryable"
    PERMANENT = "permanent"
    DEAD_LETTER = "dead_letter"


@dataclass(frozen=True)
class ToolMetadata:
    """Public capabilities and operational metadata for an engine adapter."""

    name: str
    version: str
    description: str
    supported_languages: List[str]
    health_endpoint: str = "/health"
    analyze_endpoint: str = "/analyze"
    timeout_seconds: int = 300
    failure_behavior: FailureBehavior = FailureBehavior.RETRYABLE
    license: Optional[str] = None
    source_url: Optional[str] = None


@dataclass(frozen=True)
class SourceMetadata:
    artifact_id: str
    name: str
    language: str
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None


@dataclass
class NormalizedResult:
    """Common result envelope consumed by the Arkan platform shell."""

    schema_version: str
    engine: str
    source: SourceMetadata
    entities: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        value = {
            "schema_version": self.schema_version,
            "engine": self.engine,
            "source": self.source.__dict__,
            "entities": self.entities,
            "dependencies": self.dependencies,
            "findings": self.findings,
            "artifacts": self.artifacts,
            "raw": self.raw,
            "metadata": self.metadata,
        }
        return value
