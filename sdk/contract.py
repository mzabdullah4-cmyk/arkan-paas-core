from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from .errors import AdapterValidationError
from .models import NormalizedResult, SourceMetadata, ToolMetadata


@dataclass(frozen=True)
class AdapterContext:
    """Execution context supplied by the job runner."""

    job_id: str
    source: SourceMetadata
    timeout_seconds: int
    options: Dict[str, Any]


class Adapter(ABC):
    """Contract implemented by every Arkan engine adapter.

    An adapter owns translation between the platform contract and one isolated
    OSS tool. It must not own projects, authentication, queueing, or persistence.
    """

    metadata: ToolMetadata

    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata

    def validate(self, source: SourceMetadata, content: bytes) -> None:
        """Validate input before the worker invokes the engine."""
        if not content:
            raise AdapterValidationError(self.metadata.name, "source content is empty")
        if source.language.lower() not in {language.lower() for language in self.metadata.supported_languages}:
            raise AdapterValidationError(
                self.metadata.name,
                f"unsupported language: {source.language}",
            )

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Return an engine health response."""

    @abstractmethod
    def analyze(self, content: bytes, context: AdapterContext) -> Dict[str, Any]:
        """Run the isolated engine and return its raw response."""

    @abstractmethod
    def normalize(self, raw: Dict[str, Any], context: AdapterContext) -> NormalizedResult:
        """Convert the raw engine response into the shared Arkan schema."""

    def execute(self, content: bytes, context: AdapterContext) -> NormalizedResult:
        """Validate, analyze, and normalize one artifact."""
        self.validate(context.source, content)
        raw = self.analyze(content, context)
        return self.normalize(raw, context)
