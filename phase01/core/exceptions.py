"""
Custom exception hierarchy for XENON Phase 01.
"""


class XenonException(Exception):
    """Base exception for all XENON application errors."""
    pass


class InvalidTargetError(XenonException):
    """Raised when target validation fails or target format is invalid."""
    pass


class InvalidScopeError(XenonException):
    """Raised when scope configuration or scope entries are invalid."""
    pass


class OutOfScopeError(XenonException):
    """Raised when an operation or target is determined to be out of scope."""
    pass


class ConfigurationError(XenonException):
    """Raised when configuration loading or setting fails."""
    pass


class FileOperationError(XenonException):
    """Raised when file or output operations fail."""
    pass
