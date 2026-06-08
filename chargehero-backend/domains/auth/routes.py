"""FastAPI routes for authentication domain."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from domains.auth.models import (
    RegisterRequest,
    VerifyOTPRequest,
    RegistrationResponse,
    LoginRequest,
    LoginOTPRequest,
    TokenResponse,
    UserRole,
    RegistrationStatus,
)
from domains.auth.service import AuthService
from shared.database import get_db, SupabaseDB

router = APIRouter()


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest, db: SupabaseDB = Depends(get_db)
) -> Dict[str, Any]:
    """
    Step 1: Engineer starts registration.

    Sends OTP via SMS to phone number.

    Args:
        request: Registration request with phone, email, name, dob
        db: Database dependency

    Returns:
        RegistrationResponse with registration_id and next_step

    Raises:
        HTTPException: On duplicate registration, OTP send failure, or DB error
    """
    auth_service = AuthService(db)

    # Check if phone/email already registered
    existing = (
        db.client.table("auth_engineer_registrations")
        .select("id")
        .eq("phone", request.phone)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered",
        )

    # Send OTP
    if not auth_service.send_otp(request.phone):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP",
        )

    # Create registration record
    try:
        reg = auth_service.create_registration(
            phone=request.phone,
            email=request.email,
            name=request.name,
            dob=str(request.dob),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create registration: {str(e)}",
        )

    return RegistrationResponse(
        registration_id=str(reg["id"]),
        status=RegistrationStatus(reg["status"]),
        otp_sent=True,
        next_step="verify_otp",
    )


@router.post("/register/verify-otp", response_model=RegistrationResponse)
async def verify_otp_registration(
    request: VerifyOTPRequest, db: SupabaseDB = Depends(get_db)
) -> Dict[str, Any]:
    """
    Step 2: Verify OTP.

    Marks registration as phone_verified, ready for basic info.

    Args:
        request: OTP verification request with phone and otp
        db: Database dependency

    Returns:
        RegistrationResponse with updated status

    Raises:
        HTTPException: On invalid/expired OTP or registration not found
    """
    auth_service = AuthService(db)

    # Verify OTP
    if not auth_service.verify_otp(request.phone, request.otp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    # Get registration
    reg_response = (
        db.client.table("auth_engineer_registrations")
        .select("id, status")
        .eq("phone", request.phone)
        .execute()
    )
    if not reg_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found",
        )

    return RegistrationResponse(
        registration_id=str(reg_response.data[0]["id"]),
        status=RegistrationStatus.PHONE_VERIFIED,
        next_step="submit_basic_info",
    )


@router.post("/login", response_model=RegistrationResponse)
async def login(
    request: LoginRequest, db: SupabaseDB = Depends(get_db)
) -> Dict[str, Any]:
    """
    Initiate login by sending OTP.

    Args:
        request: Login request with phone
        db: Database dependency

    Returns:
        RegistrationResponse indicating OTP was sent

    Raises:
        HTTPException: On non-existent user, OTP send failure, or DB error
    """
    auth_service = AuthService(db)

    # Verify user exists
    user_reg = auth_service.get_registration_by_phone(request.phone)
    if not user_reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Send OTP
    if not auth_service.send_otp(request.phone):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP",
        )

    return RegistrationResponse(
        registration_id=str(user_reg["id"]),
        status=RegistrationStatus(user_reg["status"]),
        otp_sent=True,
        next_step="verify_login_otp",
    )


@router.post("/login/verify-otp", response_model=TokenResponse)
async def verify_login_otp(
    request: LoginOTPRequest, db: SupabaseDB = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify login OTP and return JWT token.

    Args:
        request: Login OTP request with phone and otp
        db: Database dependency

    Returns:
        TokenResponse with access_token and user info

    Raises:
        HTTPException: On invalid/expired OTP, registration not found, or DB error
    """
    auth_service = AuthService(db)

    # Verify OTP
    if not auth_service.verify_otp(request.phone, request.otp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    # Get user registration/account
    user_reg = auth_service.get_registration_by_phone(request.phone)
    if not user_reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found",
        )

    # Create JWT token (use registration_id as user_id for now)
    token = auth_service.create_jwt_token(
        user_id=str(user_reg["id"]), role=UserRole.ENGINEER.value
    )

    # Calculate token expiry in seconds
    expires_in = settings.jwt_expiry_hours * 3600

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=str(user_reg["id"]),
        role=UserRole.ENGINEER,
        expires_in=expires_in,
    )


@router.get("/health")
async def auth_health() -> Dict[str, str]:
    """Auth domain health check.

    Returns:
        dict: Health status
    """
    return {"status": "ok", "service": "auth"}


# Import settings for token expiry calculation
from config import settings
