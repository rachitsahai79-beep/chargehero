"""Tests for error handler."""

import pytest
from fastapi import status
from shared.error_handler import (
    ChargeHeroException, ValidationError, NotFoundError, AuthenticationError,
    PermissionError, ConflictError, DatabaseError, ExternalServiceError,
    ErrorHandler, ErrorCode, ErrorSeverity
)


class TestErrorCodes:
    """Test error code enum."""

    def test_error_code_values(self):
        """Error codes have expected values."""
        assert ErrorCode.INVALID_CREDENTIALS.value == "4001"
        assert ErrorCode.NOT_FOUND.value == "4200"
        assert ErrorCode.DATABASE_ERROR.value == "5002"


class TestChargeHeroException:
    """Test base ChargeHero exception."""

    def test_exception_creation(self):
        """Create exception with message and code."""
        exc = ChargeHeroException(
            message="Test error",
            error_code=ErrorCode.INVALID_INPUT,
            severity=ErrorSeverity.LOW
        )

        assert exc.message == "Test error"
        assert exc.error_code == ErrorCode.INVALID_INPUT
        assert exc.severity == ErrorSeverity.LOW
        assert exc.timestamp is not None

    def test_exception_to_dict(self):
        """Convert exception to dictionary."""
        exc = ChargeHeroException(
            message="Test error",
            error_code=ErrorCode.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            details={"field": "email"}
        )

        error_dict = exc.to_dict()
        assert error_dict["error"] == "Test error"
        assert error_dict["error_code"] == "4100"
        assert error_dict["severity"] == "medium"
        assert error_dict["details"]["field"] == "email"

    def test_exception_status_code(self):
        """Exception has correct HTTP status code."""
        exc = ChargeHeroException(
            message="Error",
            status_code=status.HTTP_400_BAD_REQUEST
        )
        assert exc.status_code == 400


class TestValidationError:
    """Test validation error."""

    def test_validation_error_creation(self):
        """Create validation error."""
        exc = ValidationError(
            message="Invalid email format",
            details={"field": "email"}
        )

        assert exc.message == "Invalid email format"
        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert exc.severity == ErrorSeverity.LOW
        assert exc.status_code == 400

    def test_validation_error_to_dict(self):
        """Validation error dict structure."""
        exc = ValidationError("Invalid value")
        error_dict = exc.to_dict()

        assert error_dict["error_code"] == "4100"
        assert error_dict["severity"] == "low"


class TestNotFoundError:
    """Test not found error."""

    def test_not_found_error(self):
        """Create not found error."""
        exc = NotFoundError(resource="Engineer", resource_id="eng-123")

        assert "Engineer not found" in exc.message
        assert "eng-123" in exc.message
        assert exc.error_code == ErrorCode.NOT_FOUND
        assert exc.status_code == 404

    def test_not_found_error_without_id(self):
        """Create not found error without resource ID."""
        exc = NotFoundError(resource="Job")

        assert exc.message == "Job not found"


class TestAuthenticationError:
    """Test authentication error."""

    def test_auth_error_default(self):
        """Create authentication error with default message."""
        exc = AuthenticationError()

        assert exc.message == "Authentication failed"
        assert exc.error_code == ErrorCode.INVALID_CREDENTIALS
        assert exc.status_code == 401

    def test_auth_error_custom(self):
        """Create authentication error with custom message."""
        exc = AuthenticationError("Invalid token")

        assert exc.message == "Invalid token"


class TestPermissionError:
    """Test permission error."""

    def test_permission_error(self):
        """Create permission error."""
        exc = PermissionError("Only engineers can access this")

        assert exc.message == "Only engineers can access this"
        assert exc.error_code == ErrorCode.PERMISSION_DENIED
        assert exc.status_code == 403


class TestConflictError:
    """Test conflict error."""

    def test_conflict_error(self):
        """Create conflict error."""
        exc = ConflictError(resource="Email", details={"value": "test@example.com"})

        assert "Email" in exc.message
        assert exc.error_code == ErrorCode.RESOURCE_CONFLICT
        assert exc.status_code == 409


class TestDatabaseError:
    """Test database error."""

    def test_database_error(self):
        """Create database error."""
        exc = DatabaseError(
            message="Failed to insert record",
            operation="INSERT"
        )

        assert exc.message == "Failed to insert record"
        assert exc.error_code == ErrorCode.DATABASE_ERROR
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.details["operation"] == "INSERT"


class TestExternalServiceError:
    """Test external service error."""

    def test_external_service_error(self):
        """Create external service error."""
        exc = ExternalServiceError(
            service="Claude API",
            message="Rate limit exceeded"
        )

        assert "Claude API" in exc.message
        assert "Rate limit exceeded" in exc.message
        assert exc.error_code == ErrorCode.EXTERNAL_SERVICE_ERROR


class TestErrorHandler:
    """Test error handler utility."""

    def test_validate_success(self):
        """Validate condition that passes."""
        ErrorHandler.validate(True, "Should not raise")

    def test_validate_failure(self):
        """Validate condition that fails."""
        with pytest.raises(ValidationError):
            ErrorHandler.validate(False, "Validation failed")

    def test_require_found_success(self):
        """Require found with value."""
        value = "test_value"
        result = ErrorHandler.require_found(value, "Resource")
        assert result == "test_value"

    def test_require_found_failure(self):
        """Require found with None."""
        with pytest.raises(NotFoundError):
            ErrorHandler.require_found(None, "Engineer", "eng-123")

    def test_handle_chargehero_exception(self):
        """Handle ChargeHero exception."""
        exc = ValidationError("Invalid input")
        http_exc = ErrorHandler.handle_exception(exc)

        assert http_exc.status_code == 400
        assert "Invalid input" in str(http_exc.detail)

    def test_handle_unexpected_exception(self):
        """Handle unexpected exception."""
        exc = ValueError("Some error")
        http_exc = ErrorHandler.handle_exception(exc)

        assert http_exc.status_code == 500
        assert "unexpected" in str(http_exc.detail).lower()


class TestErrorSeverity:
    """Test error severity levels."""

    def test_severity_levels(self):
        """All severity levels defined."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"

    def test_severity_in_exception(self):
        """Exception stores severity."""
        exc = ChargeHeroException(
            message="Test",
            severity=ErrorSeverity.CRITICAL
        )
        assert exc.severity == ErrorSeverity.CRITICAL
