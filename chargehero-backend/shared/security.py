"""Security utilities: rate limiting, input validation, security headers."""

import logging
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Security levels for rate limiting."""
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"


class RateLimiter:
    """Simple in-memory rate limiter with TTL-based expiration."""

    def __init__(self):
        """Initialize rate limiter."""
        self.attempts: Dict[str, list] = {}

    def is_allowed(self, key: str, max_attempts: int, window_seconds: int) -> Tuple[bool, int]:
        """Check if request is within rate limit.

        Args:
            key: Unique identifier (user_id, IP, etc.)
            max_attempts: Maximum attempts allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_attempts)
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)

        if key not in self.attempts:
            self.attempts[key] = []

        # Remove expired attempts
        self.attempts[key] = [
            timestamp for timestamp in self.attempts[key]
            if timestamp > cutoff
        ]

        if len(self.attempts[key]) < max_attempts:
            self.attempts[key].append(now)
            remaining = max_attempts - len(self.attempts[key])
            return True, remaining

        remaining = max_attempts - len(self.attempts[key])
        return False, max(0, remaining)

    def reset(self, key: str) -> None:
        """Reset rate limit for key."""
        if key in self.attempts:
            del self.attempts[key]


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(max_attempts: int, window_seconds: int, key_func=None):
    """Decorator for rate limiting.

    Args:
        max_attempts: Maximum attempts allowed
        window_seconds: Time window in seconds
        key_func: Function to extract key from request (default: user_id)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract key for rate limiting
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Try to get user_id from current_user dependency
                current_user = kwargs.get('current_user', {})
                key = current_user.get('id', 'anonymous')

            is_allowed, remaining = _rate_limiter.is_allowed(
                key, max_attempts, window_seconds
            )

            if not is_allowed:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {window_seconds}s"
                )

            return await func(*args, **kwargs)

        return async_wrapper
    return decorator


class InputValidator:
    """Validate user input to prevent injection attacks."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone in E.164 format."""
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone))

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
        return bool(re.match(pattern, url)) and len(url) <= 2048

    @staticmethod
    def validate_no_sql_injection(text: str) -> bool:
        """Check for common SQL injection patterns."""
        dangerous_patterns = [
            r"('\s*OR\s*')",
            r'("\s*OR\s*")',
            r'(;\s*DROP)',
            r'(UNION\s+SELECT)',
            r'(--\s)',
            r'(/\*)',
        ]

        text_upper = text.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return False
        return True

    @staticmethod
    def validate_no_xss(text: str) -> bool:
        """Check for common XSS patterns."""
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed',
        ]

        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_lower):
                return False
        return True

    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not text:
            return ""

        # Truncate to max length
        text = text[:max_length]

        # Remove null bytes
        text = text.replace('\x00', '')

        # Remove control characters except newline/tab
        text = ''.join(
            char for char in text
            if ord(char) >= 32 or char in '\n\t'
        )

        return text.strip()

    @staticmethod
    def validate_enum(value: str, allowed_values: list) -> bool:
        """Validate value against allowed list."""
        return value in allowed_values

    @staticmethod
    def validate_integer_range(value: int, min_val: int = None, max_val: int = None) -> bool:
        """Validate integer is within range."""
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True


class PasswordSecurity:
    """Password security utilities."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt."""
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        """Validate password meets requirements.

        Requirements:
        - At least 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, None


class OTPSecurity:
    """OTP generation and verification."""

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate secure random OTP."""
        import secrets
        digits = '0123456789'
        return ''.join(secrets.choice(digits) for _ in range(length))

    @staticmethod
    def hash_otp(otp: str) -> str:
        """Hash OTP for storage."""
        return hashlib.sha256(otp.encode()).hexdigest()

    @staticmethod
    def verify_otp(provided_otp: str, hashed_otp: str) -> bool:
        """Verify OTP against hash."""
        return OTPSecurity.hash_otp(provided_otp) == hashed_otp

    @staticmethod
    def is_otp_expired(created_at: datetime, expiry_minutes: int = 5) -> bool:
        """Check if OTP has expired."""
        expiry_time = created_at + timedelta(minutes=expiry_minutes)
        return datetime.utcnow() > expiry_time


class TokenSecurity:
    """JWT token generation and verification."""

    @staticmethod
    def generate_token(user_id: str, role: str, secret_key: str, expires_hours: int = 1) -> str:
        """Generate JWT token."""
        import jwt
        from datetime import datetime, timedelta

        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow(),
        }

        return jwt.encode(payload, secret_key, algorithm='HS256')

    @staticmethod
    def verify_token(token: str, secret_key: str) -> Optional[Dict]:
        """Verify JWT token and return payload."""
        import jwt

        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None


class SecurityHeaders:
    """Security headers for HTTP responses."""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        }


class AuditLogger:
    """Log sensitive operations for audit trail."""

    @staticmethod
    def log_admin_action(admin_id: str, action: str, resource_id: str,
                        changes: Dict = None, ip_address: str = None) -> None:
        """Log admin operation."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'admin_id': admin_id,
            'action': action,
            'resource_id': resource_id,
            'changes': changes or {},
            'ip_address': ip_address,
        }

        logger.info(f"ADMIN_AUDIT: {log_entry}")

    @staticmethod
    def log_auth_attempt(user_id: str, success: bool, method: str,
                        ip_address: str = None) -> None:
        """Log authentication attempt."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'success': success,
            'method': method,
            'ip_address': ip_address,
        }

        level = "info" if success else "warning"
        getattr(logger, level)(f"AUTH_ATTEMPT: {log_entry}")

    @staticmethod
    def log_security_event(event_type: str, severity: str, details: Dict,
                          ip_address: str = None) -> None:
        """Log security event."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'ip_address': ip_address,
        }

        logger.warning(f"SECURITY_EVENT: {log_entry}")


def get_client_ip(request) -> Optional[str]:
    """Extract client IP from request."""
    # Check X-Forwarded-For header (proxy)
    if 'x-forwarded-for' in request.headers:
        return request.headers['x-forwarded-for'].split(',')[0].strip()

    # Check proxy headers
    if 'x-real-ip' in request.headers:
        return request.headers['x-real-ip']

    # Direct connection
    return request.client.host if request.client else None
