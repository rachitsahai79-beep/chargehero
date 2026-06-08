"""Pydantic models for authentication domain."""

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User roles in the system."""

    ENGINEER = "engineer"
    CUSTOMER = "customer"
    ADMIN = "admin"


class RegistrationStatus(str, Enum):
    """Registration status progression."""

    PHONE_VERIFIED = "phone_verified"
    BASIC_INFO_SUBMITTED = "basic_info_submitted"
    KYC_PENDING = "kyc_pending"
    KYC_APPROVED = "kyc_approved"
    KYC_REJECTED = "kyc_rejected"
    TRAINING_ASSIGNED = "training_assigned"
    TRAINING_COMPLETED = "training_completed"


# Request Models
class RegisterRequest(BaseModel):
    """Request model for user registration."""

    phone: str
    email: EmailStr
    name: str
    dob: date

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate Indian phone format: +919876543210 (13 chars total)."""
        if not v.startswith("+91") or len(v) != 13:
            raise ValueError(
                "Invalid Indian phone number. Format: +919876543210"
            )
        if not v[3:].isdigit():
            raise ValueError("Phone number must contain only digits after +91")
        return v

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        """Validate user is 18 years or older."""
        from datetime import date as dt

        age = (dt.today() - v).days // 365
        if age < 18:
            raise ValueError("Must be 18 years or older")
        return v


class VerifyOTPRequest(BaseModel):
    """Request model for OTP verification."""

    phone: str
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        """Validate OTP is 6 digits."""
        if not v.isdigit():
            raise ValueError("OTP must be 6 digits")
        return v


class SubmitBasicInfoRequest(BaseModel):
    """Request model for submitting basic banking information."""

    registration_id: str
    bank_account: str = Field(..., min_length=9, max_length=18)
    ifsc_code: str = Field(..., min_length=11, max_length=11)
    upi_id: str = Field(..., pattern=r"^[a-zA-Z0-9._-]+@[a-zA-Z]+$")


class LoginRequest(BaseModel):
    """Request model for login initiation."""

    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate Indian phone format."""
        if not v.startswith("+91") or len(v) != 13:
            raise ValueError(
                "Invalid Indian phone number. Format: +919876543210"
            )
        if not v[3:].isdigit():
            raise ValueError("Phone number must contain only digits after +91")
        return v


class LoginOTPRequest(BaseModel):
    """Request model for login OTP verification."""

    phone: str
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        """Validate OTP is 6 digits."""
        if not v.isdigit():
            raise ValueError("OTP must be 6 digits")
        return v


# Response Models
class RegistrationResponse(BaseModel):
    """Response model for registration operations."""

    registration_id: str
    status: RegistrationStatus
    otp_sent: Optional[bool] = None
    next_step: str


class TokenResponse(BaseModel):
    """Response model for token generation."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: UserRole
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """Response model for user information."""

    id: str
    name: str
    email: str
    phone: str
    role: UserRole
    status: str

    class Config:
        from_attributes = True
