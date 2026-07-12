class ServiceError(Exception):
    """Base class for howlite service errors."""


class NotFoundError(ServiceError):
    """Raised when a resource is not found."""
