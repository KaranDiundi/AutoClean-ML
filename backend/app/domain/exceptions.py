"""Domain-specific exceptions."""


class DomainError(Exception):
    """Base for all domain-layer errors."""


class DataIngestionError(DomainError):
    """Raised when a file cannot be loaded or parsed."""


class CleaningError(DomainError):
    """Raised when the cleaning pipeline encounters an irrecoverable issue."""


class EngineeringError(DomainError):
    """Raised when feature engineering fails."""


class ModellingError(DomainError):
    """Raised when model training fails."""


class FileNotSupportedError(DomainError):
    """Raised for unsupported file types."""
