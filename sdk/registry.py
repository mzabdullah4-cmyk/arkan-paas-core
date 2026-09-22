from typing import Any, Dict, Iterable, Optional, Type

from .contract import Adapter
from .errors import EngineNotFoundError, RegistryError


class EngineRegistry:
    """Registry for adapters available to the Arkan platform shell."""

    def __init__(self, adapters: Optional[Iterable[Adapter]] = None):
        self._adapters: Dict[str, Adapter] = {}
        for adapter in adapters or []:
            self.register(adapter)

    def register(self, adapter: Adapter) -> None:
        name = adapter.metadata.name.strip().lower()
        if not name:
            raise RegistryError("adapter name cannot be empty")
        if name in self._adapters:
            raise RegistryError(f"adapter already registered: {name}")
        self._adapters[name] = adapter

    def get(self, name: str) -> Adapter:
        key = name.strip().lower()
        try:
            return self._adapters[key]
        except KeyError as exc:
            raise EngineNotFoundError(name) from exc

    def has(self, name: str) -> bool:
        return name.strip().lower() in self._adapters

    def list(self) -> list[Dict[str, Any]]:
        return [
            {
                "name": adapter.metadata.name,
                "version": adapter.metadata.version,
                "description": adapter.metadata.description,
                "supported_languages": adapter.metadata.supported_languages,
                "health_endpoint": adapter.metadata.health_endpoint,
                "analyze_endpoint": adapter.metadata.analyze_endpoint,
                "timeout_seconds": adapter.metadata.timeout_seconds,
                "failure_behavior": adapter.metadata.failure_behavior.value,
                "license": adapter.metadata.license,
                "source_url": adapter.metadata.source_url,
            }
            for adapter in self._adapters.values()
        ]


registry = EngineRegistry()
