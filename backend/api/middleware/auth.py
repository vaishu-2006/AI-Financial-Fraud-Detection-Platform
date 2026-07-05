"""
Authentication and Authorization Service
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from enum import Enum

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SUPABASE_JWT_SECRET", "your-secret-key-change-in-production"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

class UserRole(str, Enum):
    ANALYST = "analyst"
    MANAGER = "manager"
    ADMIN = "admin"

class TokenData(BaseModel):
    user_id: str
    email: str
    role: UserRole
    exp: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.ANALYST

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    refresh_token: str

class AuthService:
    """Authentication service for JWT token management."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password for storing."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return TokenData(
                user_id=payload.get("sub"),
                email=payload.get("email"),
                role=UserRole(payload.get("role", "analyst")),
                exp=datetime.fromtimestamp(payload.get("exp", 0))
            )
        except JWTError:
            return None

    @staticmethod
    def check_permission(user_role: UserRole, required_roles: List[UserRole]) -> bool:
        """Check if user has required permissions."""
        return user_role in required_roles

def require_roles(roles: List[UserRole]):
    """Dependency for role-based access control."""
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

    security = HTTPBearer()

    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        auth_service: AuthService = Depends(lambda: AuthService())
    ):
        token_data = auth_service.decode_token(credentials.credentials)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        if not auth_service.check_permission(token_data.role, roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return token_data

    return role_checker
