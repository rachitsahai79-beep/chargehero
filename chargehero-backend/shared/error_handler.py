"""Error handling and custom exceptions for ChargeHero."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    # Authentication errors (4000-4099)
    INVALID_CREDENTIALS = "4001"
    TOKEN_EXPIRED = "4002"
    TOKEN_INVALID = "4003"
    UNAUTHORIZED = "4004"
    PERMISSION_DENIED = "4005"

    # Validation errors (4100-4199)
    VALIDATION_ERROR = "4100"
    INVALID_INPUT = "4101"
    MISSING_REQUIRED_FIELD = "4102"
    INVALID_FORMAT = "4103"

    # Resource errors (4200-4299)
    NOT_FOUND = "4200"
    ALREADY_EXISTS = "4201"
    RESOURCE_CONFLICT = "4202"
    DELETED_RESOURCE = "4203"

    # Service errors (5000-5099)
    SERVICE_UNAVAILABLE = "5001"
    DATABASE_ERROR = "5002"
    EXTERNAL_SERVICE_ERROR = "5003"
    TIMEOUT = "5004"

    # Application errors (5100-5199)
    INTERNAL_ERROR = "5100"
    NOT_IMPLEMENTED = "5101"
    INVALID_STATE = "5102"


class ChargeHeroException(Exception):
    """Base exception for ChargeHero application."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        """Initialize exception."""
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = datetime.utcnow().isoformat()

        super().__init__(self.message)

        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"[{error_code}] {message}", extra={"details": self.details})
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"[{error_code}] {message}", extra={"details": self.details})
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"[{error_code}] {message}", extra={"details": self.details})
        else:
            logger.info(f"[{error_code}] {message}", extra={"details": self.details})

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": self.message,
            "error_code": self.error_code.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "details": self.details
        }


class ValidationError(ChargeHeroException):
    """Exception for validation errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize validation error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            severity=ErrorSeverity.LOW,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class NotFoundError(ChargeHeroException):
    """Exception for not found errors."""

    def __init__(
        self,
        resource: str,
        resource_id: Optional[str] = None,
    ):
        """Initialize not found error."""
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"

        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            details={"resource": resource, "resource_id": resource_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )


class AuthenticationError(ChargeHeroException):
    """Exception for authentication errors."""

    def __init__(self, message: str = "Authentication failed"):
        """Initialize authentication error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_CREDENTIALS,
            severity=ErrorSeverity.MEDIUM,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class PermissionError(ChargeHeroException):
    """Exception for permission errors."""

    def __init__(self, message: str = "Permission denied"):
        """Initialize permission error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.PERMISSION_DENIED,
            severity=ErrorSeverity.MEDIUM,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictError(ChargeHeroException):
    """Exception for conflict errors."""

    def __init__(
        self,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize conflict error."""
        super().__init__(
            message=f"{resource} already exists or conflicts",
            error_code=ErrorCode.RESOURCE_CONFLICT,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            status_code=status.HTTP_409_CONFLICT,
        )


class DatabaseError(ChargeHeroException):
    """Exception for database errors."""

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
    ):
        """Initialize database error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            severity=ErrorSeverity.HIGH,
            details={"operation": operation},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ExternalServiceError(ChargeHeroException):
    """Exception for external service errors."""

    def __init__(
        self,
        service: str,
        message: str = "External service error",
    ):
        """Initialize external service error."""
        super().__init__(
            message=f"{service}: {message}",
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            severity=ErrorSeverity.HIGH,
            details={"service": service},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class ErrorHandler:
    """Central error handler for the application."""

    @staticmethod
    def handle_exception(exc: Exception) -> HTTPException:
        """Convert any exception to HTTPException."""
        if isinstance(exc, ChargeHeroException):
            logger.log(
                logging.ERROR if exc.severity.value != "critical" else logging.CRITICAL,
                f"Returning HTTP {exc.status_code}: {exc.to_dict()}"
            )
            return HTTPException(
                status_code=exc.status_code,
                detail=exc.to_dict()
            )

        # Handle unexpected exceptions
        logger.exception("Unexpected exception occurred")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "An unexpected error occurred",
                "error_code": ErrorCode.INTERNAL_ERROR.value,
                "severity": ErrorSeverity.CRITICAL.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @staticmethod
    def validate(condition: bool, message: str, details: Optional[Dict[str, Any]] = None):
        """Raise ValidationError if condition is false."""
        if not condition:
            raise ValidationError(message, details)

    @staticmethod
    def require_found(value: Any, resource: str, resource_id: Optional[str] = None):
        """Raise NotFoundError if value is None."""
        if value is None:
            raise NotFoundError(resource, resource_id)
        return value


class RequestLogger:
    """Structured request logging."""

    @staticmethod
    def log_request(method: str, path: str, user_id: Optional[str] = None):
        """Log incoming request."""
        logger.info(
            f"Request: {method} {path}",
            extra={"user_id": user_id, "method": method, "path": path}
        )

    @staticmethod
    def log_response(method: str, path: str, status_code: int, duration_ms: float, user_id: Optional[str] = None):
        """Log outgoing response."""
        log_level = logging.WARNING if status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            f"Response: {method} {path} - {status_code} ({duration_ms:.2f}ms)",
            extra={
                "user_id": user_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms
            }
        )

    @staticmethod
    def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log error with context."""
        logger.exception(
            f"Error: {str(error)}",
            extra=context or {}
        )
