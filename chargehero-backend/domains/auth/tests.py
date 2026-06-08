"""Unit tests for authentication domain."""

import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from pydantic import ValidationError

from domains.auth.models import (
    RegisterRequest,
    VerifyOTPRequest,
    LoginRequest,
    LoginOTPRequest,
    SubmitBasicInfoRequest,
    UserRole,
    RegistrationStatus,
)
from domains.auth.service import AuthService


@pytest.fixture
def mock_db():
    """Mock database for testing."""
    db = MagicMock()
    db.client = MagicMock()
    return db


@pytest.fixture
def auth_service(mock_db):
    """Create auth service with mock DB."""
    return AuthService(mock_db)


# ============================================================================
# OTP Generation and Verification Tests
# ============================================================================


class TestOTPGeneration:
    """Tests for OTP generation."""

    def test_generate_otp_length(self, auth_service):
        """OTP should be 6 characters long."""
        otp = auth_service.generate_otp()
        assert len(otp) == 6

    def test_generate_otp_is_digit(self, auth_service):
        """OTP should contain only digits."""
        otp = auth_service.generate_otp()
        assert otp.isdigit()

    def test_generate_otp_uniqueness(self, auth_service):
        """Multiple OTP generations should produce different values (with high probability)."""
        otps = [auth_service.generate_otp() for _ in range(10)]
        # Very unlikely all 10 random 6-digit numbers are the same
        assert len(set(otps)) > 1


class TestOTPVerification:
    """Tests for OTP verification."""

    def test_verify_otp_success(self, auth_service):
        """OTP verification should succeed with correct OTP."""
        phone = "+919876543210"
        auth_service.send_otp(phone)

        stored_otp = auth_service._otp_store[phone]["otp"]
        assert auth_service.verify_otp(phone, stored_otp) is True

    def test_verify_otp_invalid(self, auth_service):
        """OTP verification should fail with wrong OTP."""
        phone = "+919876543210"
        auth_service.send_otp(phone)

        assert auth_service.verify_otp(phone, "000000") is False

    def test_verify_otp_nonexistent_phone(self, auth_service):
        """OTP verification should fail for non-existent phone."""
        assert auth_service.verify_otp("+919876543210", "123456") is False

    def test_verify_otp_expired(self, auth_service):
        """OTP verification should fail after 5 minutes."""
        phone = "+919876543210"
        auth_service.send_otp(phone)

        # Manually expire the OTP
        auth_service._otp_store[phone]["created_at"] = (
            datetime.now(timezone.utc) - timedelta(minutes=6)
        )

        assert auth_service.verify_otp(phone, "123456") is False
        # Expired OTP should be removed
        assert phone not in auth_service._otp_store

    def test_verify_otp_max_attempts(self, auth_service):
        """OTP should be invalidated after 3 wrong attempts."""
        phone = "+919876543210"
        auth_service.send_otp(phone)
        stored_otp = auth_service._otp_store[phone]["otp"]

        # Try wrong OTP 3 times
        for _ in range(3):
            auth_service.verify_otp(phone, "000000")

        # Phone should be removed after 3 attempts
        assert phone not in auth_service._otp_store

    def test_otp_removed_after_verification(self, auth_service):
        """OTP should be removed from store after successful verification."""
        phone = "+919876543210"
        auth_service.send_otp(phone)
        stored_otp = auth_service._otp_store[phone]["otp"]

        auth_service.verify_otp(phone, stored_otp)
        assert phone not in auth_service._otp_store


# ============================================================================
# JWT Token Tests
# ============================================================================


class TestJWTToken:
    """Tests for JWT token creation and verification."""

    def test_create_jwt_token(self, auth_service):
        """JWT token should be created and decodable."""
        token = auth_service.create_jwt_token("user-123", "engineer")
        assert token is not None
        assert isinstance(token, str)

    def test_verify_jwt_token_valid(self, auth_service):
        """Valid JWT token should decode successfully."""
        user_id = "user-123"
        role = "engineer"
        token = auth_service.create_jwt_token(user_id, role)

        payload = auth_service.verify_jwt_token(token)
        assert payload["sub"] == user_id
        assert payload["role"] == role

    def test_verify_jwt_token_invalid(self, auth_service):
        """Invalid token should raise exception."""
        with pytest.raises(Exception, match="Invalid token"):
            auth_service.verify_jwt_token("invalid.token.string")

    def test_verify_jwt_token_expired(self, auth_service):
        """Expired token should raise exception."""
        import jwt as jwt_lib
        from config import settings

        # Create an expired token
        expired_payload = {
            "sub": "user-123",
            "role": "engineer",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        expired_token = jwt_lib.encode(
            expired_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
        )

        with pytest.raises(Exception, match="expired"):
            auth_service.verify_jwt_token(expired_token)

    def test_jwt_token_has_sub_claim(self, auth_service):
        """JWT token should contain 'sub' (subject/user_id) claim."""
        token = auth_service.create_jwt_token("user-456", "customer")
        payload = auth_service.verify_jwt_token(token)
        assert "sub" in payload

    def test_jwt_token_has_role_claim(self, auth_service):
        """JWT token should contain 'role' claim."""
        token = auth_service.create_jwt_token("user-456", "customer")
        payload = auth_service.verify_jwt_token(token)
        assert "role" in payload

    def test_jwt_token_has_exp_claim(self, auth_service):
        """JWT token should contain 'exp' (expiration) claim."""
        token = auth_service.create_jwt_token("user-456", "customer")
        payload = auth_service.verify_jwt_token(token)
        assert "exp" in payload

    def test_jwt_token_has_iat_claim(self, auth_service):
        """JWT token should contain 'iat' (issued at) claim."""
        token = auth_service.create_jwt_token("user-456", "customer")
        payload = auth_service.verify_jwt_token(token)
        assert "iat" in payload


# ============================================================================
# Registration Model Validation Tests
# ============================================================================


class TestRegisterRequestValidation:
    """Tests for RegisterRequest model validation."""

    def test_valid_registration(self):
        """Valid registration request should be accepted."""
        valid = RegisterRequest(
            phone="+919876543210",
            email="engineer@example.com",
            name="John Doe",
            dob=date(2000, 1, 1),
        )
        assert valid.phone == "+919876543210"
        assert valid.email == "engineer@example.com"
        assert valid.name == "John Doe"

    def test_invalid_phone_format(self):
        """Phone number without +91 prefix should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                phone="9876543210",
                email="engineer@example.com",
                name="John Doe",
                dob=date(2000, 1, 1),
            )
        assert "phone" in str(exc_info.value)

    def test_invalid_phone_length(self):
        """Phone number with incorrect length should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                phone="+91987654321",  # 12 chars instead of 13
                email="engineer@example.com",
                name="John Doe",
                dob=date(2000, 1, 1),
            )
        assert "phone" in str(exc_info.value)

    def test_invalid_phone_non_digits(self):
        """Phone number with non-digit characters should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                phone="+91987654321a",
                email="engineer@example.com",
                name="John Doe",
                dob=date(2000, 1, 1),
            )
        assert "phone" in str(exc_info.value)

    def test_invalid_email(self):
        """Invalid email format should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                phone="+919876543210",
                email="not-an-email",
                name="John Doe",
                dob=date(2000, 1, 1),
            )
        assert "email" in str(exc_info.value)

    def test_user_too_young(self):
        """Users under 18 should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                phone="+919876543210",
                email="engineer@example.com",
                name="John Doe",
                dob=date.today().replace(year=date.today().year - 17),
            )
        assert "dob" in str(exc_info.value)

    def test_user_exactly_18(self):
        """Users exactly 18 years old should be accepted."""
        # Create a date 18 years ago
        dob = date.today().replace(year=date.today().year - 18)
        valid = RegisterRequest(
            phone="+919876543210",
            email="engineer@example.com",
            name="John Doe",
            dob=dob,
        )
        assert valid.dob == dob


# ============================================================================
# OTP Request Model Validation Tests
# ============================================================================


class TestVerifyOTPRequestValidation:
    """Tests for VerifyOTPRequest model validation."""

    def test_valid_otp_request(self):
        """Valid OTP request should be accepted."""
        valid = VerifyOTPRequest(phone="+919876543210", otp="123456")
        assert valid.otp == "123456"

    def test_invalid_otp_length_short(self):
        """OTP shorter than 6 digits should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            VerifyOTPRequest(phone="+919876543210", otp="12345")
        assert "otp" in str(exc_info.value)

    def test_invalid_otp_length_long(self):
        """OTP longer than 6 digits should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            VerifyOTPRequest(phone="+919876543210", otp="1234567")
        assert "otp" in str(exc_info.value)

    def test_invalid_otp_non_digits(self):
        """OTP with non-digit characters should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            VerifyOTPRequest(phone="+919876543210", otp="12345a")
        assert "otp" in str(exc_info.value)


# ============================================================================
# Login Request Model Validation Tests
# ============================================================================


class TestLoginRequestValidation:
    """Tests for LoginRequest model validation."""

    def test_valid_login_request(self):
        """Valid login request should be accepted."""
        valid = LoginRequest(phone="+919876543210")
        assert valid.phone == "+919876543210"

    def test_invalid_login_phone_format(self):
        """Invalid phone format in login should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(phone="9876543210")
        assert "phone" in str(exc_info.value)


# ============================================================================
# Integration Tests (with mock DB)
# ============================================================================


class TestRegistrationCreation:
    """Tests for registration creation."""

    def test_create_registration_success(self, auth_service, mock_db):
        """Registration should be created successfully."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": "reg-123",
                "phone": "+919876543210",
                "email": "engineer@example.com",
                "name": "John Doe",
                "dob": "2000-01-01",
                "status": "phone_verified",
            }
        ]

        mock_db.client.table.return_value.insert.return_value.execute.return_value = (
            mock_response
        )

        result = auth_service.create_registration(
            phone="+919876543210",
            email="engineer@example.com",
            name="John Doe",
            dob="2000-01-01",
        )

        assert result["id"] == "reg-123"
        assert result["status"] == "phone_verified"

    def test_create_registration_failure(self, auth_service, mock_db):
        """Registration creation should raise exception on failure."""
        mock_response = MagicMock()
        mock_response.data = []

        mock_db.client.table.return_value.insert.return_value.execute.return_value = (
            mock_response
        )

        with pytest.raises(Exception):
            auth_service.create_registration(
                phone="+919876543210",
                email="engineer@example.com",
                name="John Doe",
                dob="2000-01-01",
            )


class TestRegistrationRetrieval:
    """Tests for registration retrieval."""

    def test_get_registration_by_phone(self, auth_service, mock_db):
        """Registration should be retrieved by phone number."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": "reg-123",
                "phone": "+919876543210",
                "email": "engineer@example.com",
                "name": "John Doe",
                "status": "phone_verified",
            }
        ]

        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        result = auth_service.get_registration_by_phone("+919876543210")
        assert result is not None
        assert result["id"] == "reg-123"

    def test_get_registration_not_found(self, auth_service, mock_db):
        """Should return None when registration not found."""
        mock_response = MagicMock()
        mock_response.data = []

        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        result = auth_service.get_registration_by_phone("+919876543210")
        assert result is None


# ============================================================================
# SubmitBasicInfoRequest Validation Tests
# ============================================================================


class TestSubmitBasicInfoValidation:
    """Tests for SubmitBasicInfoRequest model validation."""

    def test_valid_basic_info(self):
        """Valid basic info request should be accepted."""
        valid = SubmitBasicInfoRequest(
            registration_id="reg-123",
            bank_account="123456789",
            ifsc_code="SBIN0000001",
            upi_id="user@bank",
        )
        assert valid.bank_account == "123456789"

    def test_invalid_bank_account_short(self):
        """Bank account shorter than 9 digits should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SubmitBasicInfoRequest(
                registration_id="reg-123",
                bank_account="12345678",
                ifsc_code="SBIN0000001",
                upi_id="user@bank",
            )
        assert "bank_account" in str(exc_info.value)

    def test_invalid_ifsc_code_length(self):
        """IFSC code must be exactly 11 characters."""
        with pytest.raises(ValidationError) as exc_info:
            SubmitBasicInfoRequest(
                registration_id="reg-123",
                bank_account="123456789",
                ifsc_code="SBIN000001",  # 10 chars
                upi_id="user@bank",
            )
        assert "ifsc_code" in str(exc_info.value)

    def test_invalid_upi_id_format(self):
        """UPI ID with invalid format should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SubmitBasicInfoRequest(
                registration_id="reg-123",
                bank_account="123456789",
                ifsc_code="SBIN0000001",
                upi_id="invalid-upi",  # Missing @
            )
        assert "upi_id" in str(exc_info.value)

    def test_valid_upi_id_variations(self):
        """Various valid UPI ID formats should be accepted."""
        valid_upis = [
            "user@bank",
            "user123@bank",
            "user_name@bank",
            "user-name@bank",
            "user.name@bank",
        ]
        for upi in valid_upis:
            request = SubmitBasicInfoRequest(
                registration_id="reg-123",
                bank_account="123456789",
                ifsc_code="SBIN0000001",
                upi_id=upi,
            )
            assert request.upi_id == upi
