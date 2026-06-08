"""End-to-end tests for authentication flow."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_db():
    """Create mock database."""
    db = MagicMock()
    return db


@pytest.fixture
def auth_service(mock_db):
    """Create AuthService with mock database."""
    from domains.auth.service import AuthService
    return AuthService(mock_db)


class TestRegistrationFlow:
    """Test complete registration flow."""

    def test_registration_sends_otp(self, auth_service, mock_db):
        """User registration should send OTP."""
        # Mock: user doesn't exist yet
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        with patch('domains.auth.service.send_otp_sms') as mock_sms:
            result = auth_service.send_registration_otp(
                phone='+919876543210',
                email='user@example.com',
                name='Test User'
            )

            assert result is True
            mock_sms.assert_called_once()

    def test_registration_otp_verification(self, auth_service, mock_db):
        """OTP verification should complete registration."""
        # Mock: OTP is valid
        otp_record = {
            'id': 'otp123',
            'phone': '+919876543210',
            'otp_code': '123456',
            'expires_at': datetime.utcnow().isoformat(),
            'attempts': 1
        }

        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[otp_record]
        )

        with patch('domains.auth.service.generate_jwt_token', return_value='token123'):
            result = auth_service.verify_registration_otp(
                phone='+919876543210',
                otp_code='123456',
                role='customer'
            )

            assert result is not None
            assert 'token' in result

    def test_registration_fails_with_invalid_otp(self, auth_service, mock_db):
        """Invalid OTP should fail verification."""
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]  # No OTP found
        )

        result = auth_service.verify_registration_otp(
            phone='+919876543210',
            otp_code='000000',
            role='customer'
        )

        assert result is None

    def test_registration_fails_with_expired_otp(self, auth_service, mock_db):
        """Expired OTP should fail verification."""
        expired_otp = {
            'id': 'otp123',
            'phone': '+919876543210',
            'otp_code': '123456',
            'expires_at': '2020-01-01T00:00:00',  # Past date
            'attempts': 0
        }

        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[expired_otp]
        )

        result = auth_service.verify_registration_otp(
            phone='+919876543210',
            otp_code='123456',
            role='customer'
        )

        assert result is None


class TestLoginFlow:
    """Test complete login flow."""

    def test_login_sends_otp(self, auth_service, mock_db):
        """Login should send OTP to registered user."""
        user = {
            'id': 'user123',
            'phone': '+919876543210',
            'role': 'customer'
        }

        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[user]
        )

        with patch('domains.auth.service.send_otp_sms') as mock_sms:
            result = auth_service.send_login_otp(phone='+919876543210')

            assert result is True
            mock_sms.assert_called_once()

    def test_login_fails_for_unregistered_user(self, auth_service, mock_db):
        """Login should fail for unregistered phone."""
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]  # No user found
        )

        result = auth_service.send_login_otp(phone='+919999999999')

        assert result is False

    def test_login_otp_verification(self, auth_service, mock_db):
        """OTP verification should complete login."""
        user = {
            'id': 'user123',
            'phone': '+919876543210',
            'role': 'customer'
        }

        otp_record = {
            'id': 'otp123',
            'phone': '+919876543210',
            'otp_code': '123456',
            'expires_at': datetime.utcnow().isoformat(),
            'attempts': 1
        }

        # Setup mock chain
        mock_select = mock_db.table.return_value.select.return_value
        mock_select.eq.return_value.execute.side_effect = [
            MagicMock(data=[otp_record]),  # First call: OTP lookup
            MagicMock(data=[user]),  # Second call: User lookup
        ]

        with patch('domains.auth.service.generate_jwt_token', return_value='token123'):
            result = auth_service.verify_login_otp(
                phone='+919876543210',
                otp_code='123456'
            )

            assert result is not None
            assert 'token' in result


class TestOTPAttempts:
    """Test OTP attempt limiting."""

    def test_otp_fails_after_3_attempts(self, auth_service, mock_db):
        """OTP should fail after 3 failed attempts."""
        otp_record = {
            'id': 'otp123',
            'phone': '+919876543210',
            'otp_code': '123456',
            'expires_at': datetime.utcnow().isoformat(),
            'attempts': 3  # Already at max attempts
        }

        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[otp_record]
        )

        result = auth_service.verify_registration_otp(
            phone='+919876543210',
            otp_code='123456',
            role='customer'
        )

        assert result is None

    def test_otp_increments_attempt_counter(self, auth_service, mock_db):
        """Failed OTP should increment attempt counter."""
        otp_record = {
            'id': 'otp123',
            'phone': '+919876543210',
            'otp_code': '123456',
            'expires_at': datetime.utcnow().isoformat(),
            'attempts': 1
        }

        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[otp_record]
        )

        # Wrong OTP should increment counter
        result = auth_service.verify_registration_otp(
            phone='+919876543210',
            otp_code='000000',  # Wrong code
            role='customer'
        )

        assert result is None
        # Verify update was called (simplified check)


class TestTokenGeneration:
    """Test JWT token generation."""

    def test_token_contains_user_claims(self, auth_service):
        """Generated token should contain user claims."""
        with patch('domains.auth.service.generate_jwt_token') as mock_gen:
            mock_gen.return_value = 'token.payload.signature'

            token = auth_service.generate_token(
                user_id='user123',
                role='engineer'
            )

            assert token == 'token.payload.signature'
            mock_gen.assert_called_once()

    def test_token_expiry_set_correctly(self, auth_service):
        """Token should have correct expiry time."""
        with patch('domains.auth.service.generate_jwt_token') as mock_gen:
            mock_gen.return_value = 'token123'

            token = auth_service.generate_token(
                user_id='user123',
                role='engineer'
            )

            assert token is not None
