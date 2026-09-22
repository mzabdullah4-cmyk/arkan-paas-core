class AdapterError(Exception):
    """Base error raised by an Arkan adapter."""

    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class AdapterValidationError(AdapterError):
    def __init__(self, engine: str, message: str):
        super().__init__(f"{engine} input validation failed: {message}", retryable=False)
        self.engine = engine


class AdapterExecutionError(AdapterError):
    def __init__(self, engine: str, message: str, *, retryable: bool = True):
        super().__init__(f"{engine} execution failed: {message}", retryable=retryable)
        self.engine = engine


class RegistryError(AdapterError):
    pass


class EngineNotFoundError(RegistryError):
    def __init__(self, engine: str):
        super().__init__(f"engine adapter not found: {engine}")
        self.engine = engine
