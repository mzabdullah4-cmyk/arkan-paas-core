"""Arkan Adapter SDK.

The SDK is intentionally dependency-light so adapters can run inside isolated
worker containers without importing the control plane.
"""

from .contract import Adapter, AdapterContext
from .errors import AdapterError, AdapterValidationError, EngineNotFoundError, RegistryError
from .models import FailureBehavior, NormalizedResult, SourceMetadata, ToolMetadata
from .registry import EngineRegistry, registry

__all__ = [
    "Adapter",
    "AdapterContext",
    "AdapterError",
    "AdapterValidationError",
    "EngineNotFoundError",
    "EngineRegistry",
    "FailureBehavior",
    "NormalizedResult",
    "SourceMetadata",
    "ToolMetadata",
    "RegistryError",
    "registry",
]
