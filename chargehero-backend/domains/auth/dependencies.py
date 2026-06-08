"""Dependency injection for authentication domain."""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from domains.auth.service import AuthService
from shared.database import get_db, SupabaseDB
from typing import Dict, Any

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: SupabaseDB = Depends(get_db),
) -> Dict[str, Any]:
    """
    Dependency to extract and verify current user from JWT.

    Extracts JWT token from Authorization header, verifies it, and returns
    user information from the payload.

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database dependency

    Returns:
        Dictionary with user_id and role

    Raises:
        HTTPException: If token is invalid, expired, or missing required claims
    """
    auth_service = AuthService(db)

    try:
        payload = auth_service.verify_jwt_token(credentials.credentials)
        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        return {"user_id": user_id, "role": role}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Dependency to ensure current user is admin.

    Wraps get_current_user and adds authorization check for admin role.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        Dictionary with user_id and role (if authorized)

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_engineer_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Dependency to ensure current user is an engineer.

    Wraps get_current_user and adds authorization check for engineer role.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        Dictionary with user_id and role (if authorized)

    Raises:
        HTTPException: If user is not an engineer
    """
    if current_user.get("role") != "engineer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer access required",
        )
    return current_user
