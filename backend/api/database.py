"""
Database connection using Supabase
"""
import os
from typing import Optional
from supabase import create_client, Client
from functools import lru_cache

@lru_cache()
def get_supabase_client() -> Client:
    """Get cached Supabase client instance."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

    return create_client(url, key)

async def get_current_user(supabase: Client, token: str) -> Optional[dict]:
    """Verify JWT token and get current user."""
    try:
        user = supabase.auth.get_user(token)
        if user and user.user:
            return user.user.model_dump()
    except Exception:
        pass
    return None
