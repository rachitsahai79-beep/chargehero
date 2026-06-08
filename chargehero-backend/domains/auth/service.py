"""Authentication service with OTP, JWT, and user management."""

import random
import string
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from config import settings
from shared.database import SupabaseDB

logger = logging.getLogger(__name__)


class AuthService:
    """Handle authentication operations: OTP, JWT, registration."""

    # In-memory OTP store (use Redis in production)
    _otp_store: Dict[str, Dict[str, Any]] = {}

    def __init__(self, db: SupabaseDB):
        """Initialize auth service with database instance.

        Args:
            db: SupabaseDB instance for database operations
        """
        self.db = db

    @staticmethod
    def generate_otp() -> str:
        """Generate 6-digit OTP.

        Returns:
            String of 6 random digits
        """
        return "".join(random.choices(string.digits, k=6))

    def send_otp(self, phone: str) -> bool:
        """Send OTP via SMS using Twilio.

        Args:
            phone: Phone number in format +919876543210

        Returns:
            True if OTP sent successfully, False otherwise
        """
        otp = self.generate_otp()
        self._otp_store[phone] = {
            "otp": otp,
            "created_at": datetime.now(timezone.utc),
            "attempts": 0,
        }

        try:
            # TODO: Integrate Twilio for SMS sending
            # For now, just log it (in dev/test)
            logger.info(
                f"OTP for {phone}: {otp} (DEV MODE - not actually sending SMS)"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending OTP: {e}")
            return False

    def verify_otp(self, phone: str, otp: str) -> bool:
        """Verify OTP and remove from store.

        Args:
            phone: Phone number in format +919876543210
            otp: 6-digit OTP from user

        Returns:
            True if OTP is valid, False otherwise
        """
        if phone not in self._otp_store:
            logger.warning(
                f"OTP verification attempt for non-existent phone: {phone}"
            )
            return False

        stored = self._otp_store[phone]

        # Check expiration (5 minutes)
        if (
            datetime.now(timezone.utc) - stored["created_at"]
            > timedelta(minutes=5)
        ):
            del self._otp_store[phone]
            logger.warning(f"OTP expired for {phone}")
            return False

        # Check OTP match
        if stored["otp"] != otp:
            stored["attempts"] += 1
            if stored["attempts"] >= 3:
                del self._otp_store[phone]
                logger.warning(f"OTP verification failed 3 times for {phone}")
            return False

        # Valid OTP - clean up
        del self._otp_store[phone]
        logger.info(f"OTP verified successfully for {phone}")
        return True

    def create_registration(
        self, phone: str, email: str, name: str, dob: str
    ) -> Dict[str, Any]:
        """Create new engineer registration.

        Args:
            phone: Phone number in format +919876543210
            email: Email address
            name: User's full name
            dob: Date of birth in YYYY-MM-DD format

        Returns:
            Dictionary containing registration data

        Raises:
            Exception: If registration creation fails
        """
        try:
            response = (
                self.db.client.table("auth_engineer_registrations")
                .insert(
                    {
                        "phone": phone,
                        "email": email,
                        "name": name,
                        "dob": dob,
                        "status": "phone_verified",
                    }
                )
                .execute()
            )

            if response.data:
                logger.info(f"Registration created for {phone}")
                return response.data[0]
            else:
                logger.error("Failed to create registration: empty response")
                raise Exception("Failed to create registration")
        except Exception as e:
            logger.error(f"Error creating registration: {e}")
            raise

    def get_registration(self, registration_id: str) -> Optional[Dict[str, Any]]:
        """Get registration by ID.

        Args:
            registration_id: Registration record ID

        Returns:
            Registration data or None if not found
        """
        try:
            response = (
                self.db.client.table("auth_engineer_registrations")
                .select("*")
                .eq("id", registration_id)
                .execute()
            )

            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching registration: {e}")
            return None

    def get_registration_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get registration by phone number.

        Args:
            phone: Phone number in format +919876543210

        Returns:
            Registration data or None if not found
        """
        try:
            response = (
                self.db.client.table("auth_engineer_registrations")
                .select("*")
                .eq("phone", phone)
                .execute()
            )

            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching registration by phone: {e}")
            return None

    def update_registration(
        self, registration_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update registration data.

        Args:
            registration_id: Registration record ID
            data: Dictionary of fields to update

        Returns:
            Updated registration data or None if update fails
        """
        try:
            response = (
                self.db.client.table("auth_engineer_registrations")
                .update(data)
                .eq("id", registration_id)
                .execute()
            )

            if response.data:
                logger.info(f"Registration {registration_id} updated")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating registration: {e}")
            return None

    def create_jwt_token(self, user_id: str, role: str) -> str:
        """Create JWT token.

        Args:
            user_id: User ID to encode in token
            role: User role (engineer, customer, admin)

        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        expiration = now + timedelta(hours=settings.jwt_expiry_hours)

        payload = {
            "sub": user_id,  # Subject (user_id)
            "role": role,
            "iat": now,  # Issued at
            "exp": expiration,  # Expiration
        }

        token = jwt.encode(
            payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
        )
        logger.info(f"JWT token created for user {user_id}")
        return token

    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dictionary

        Raises:
            Exception: If token is expired or invalid
        """
        try:
            payload = jwt.decode(
                token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise Exception("Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise Exception("Invalid token")
