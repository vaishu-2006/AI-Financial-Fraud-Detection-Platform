"""
Authentication Routes
"""
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
from supabase import Client

from api.database import get_supabase_client
from api.middleware.auth import (
    AuthService, UserCreate, UserLogin, Token, TokenData,
    TokenRefresh, UserRole, require_roles
)

router = APIRouter()
security = HTTPBearer()

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    department: Optional[str]
    is_active: bool
    created_at: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, request: Request):
    """
    Register a new user account.

    - **email**: Valid email address
    - **password**: Minimum 8 characters, must contain uppercase, lowercase, and number
    - **full_name**: User's full name
    - **role**: User role (analyst, manager, admin)
    """
    supabase: Client = request.app.state.supabase

    # Check if user exists
    existing = supabase.table("users").select("id").eq("email", user_data.email).maybe_single().execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )

    # Create auth user with Supabase Auth
    try:
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
        })

        if auth_response.user:
            # Create profile in users table
            profile = supabase.table("users").insert({
                "id": auth_response.user.id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "role": user_data.role.value
            }).execute()

            return UserResponse(
                id=auth_response.user.id,
                email=user_data.email,
                full_name=user_data.full_name,
                role=user_data.role.value,
                is_active=True
            )
    except Exception as e:
        # If Supabase auth fails, clean up
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, request: Request):
    """
    Authenticate user and receive access tokens.

    Returns:
    - **access_token**: JWT token for API requests (expires in 1 hour)
    - **refresh_token**: Token to refresh access (expires in 7 days)
    - **token_type**: "bearer"
    - **expires_in**: Token expiration in seconds
    """
    supabase: Client = request.app.state.supabase
    auth_service = request.app.state.auth_service

    try:
        # Authenticate with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })

        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Get user profile for role
        profile = supabase.table("users").select("role").eq("id", auth_response.user.id).maybe_single().execute()
        role = profile.data.get("role", "analyst") if profile.data else "analyst"

        # Create our own JWT with role info
        token_data = {
            "sub": auth_response.user.id,
            "email": user_data.email,
            "role": role
        }

        access_token = auth_service.create_access_token(token_data)
        refresh_token = auth_service.create_refresh_token({"sub": auth_response.user.id})

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh, request: Request):
    """
    Refresh access token using refresh token.

    Provide a valid refresh token to receive new access and refresh tokens.
    """
    supabase: Client = request.app.state.supabase
    auth_service = request.app.state.auth_service

    # Decode refresh token
    decoded = auth_service.decode_token(token_data.refresh_token)
    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Get user profile for role
    profile = supabase.table("users").select("role, email").eq("id", decoded.user_id).maybe_single().execute()
    if not profile.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new tokens
    new_token_data = {
        "sub": decoded.user_id,
        "email": profile.data["email"],
        "role": profile.data.get("role", "analyst")
    }

    access_token = auth_service.create_access_token(new_token_data)
    refresh_token = auth_service.create_refresh_token({"sub": decoded.user_id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600
    )

@router.post("/logout")
async def logout(request: Request, credentials = Depends(security)):
    """Logout and invalidate current session."""
    supabase: Client = request.app.state.supabase
    try:
        supabase.auth.sign_out()
    except:
        pass
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserProfile)
async def get_current_user_info(request: Request, token_data: TokenData = Depends(require_roles([UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]))):
    """Get current authenticated user's profile."""
    supabase: Client = request.app.state.supabase

    profile = supabase.table("users").select("*").eq("id", token_data.user_id).maybe_single().execute()
    if not profile.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    return UserProfile(**profile.data)

@router.get("/users", response_model=list[UserResponse])
async def list_users(request: Request, token_data: TokenData = Depends(require_roles([UserRole.ADMIN]))):
    """List all users (Admin only)."""
    supabase: Client = request.app.state.supabase
    result = supabase.table("users").select("id, email, full_name, role, is_active").execute()
    return result.data

@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: UserRole,
    request: Request,
    token_data: TokenData = Depends(require_roles([UserRole.ADMIN]))
):
    """Update user's role (Admin only)."""
    supabase: Client = request.app.state.supabase
    result = supabase.table("users").update({"role": role.value}).eq("id", user_id).execute()
    return {"message": "Role updated", "user_id": user_id, "new_role": role.value}
