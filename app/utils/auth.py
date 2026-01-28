"""
Authentication utilities for API token verification.
"""
import os
from fastapi import Header, HTTPException, status
from typing import Optional


def get_api_token() -> Optional[str]:
    """Get API token from environment variable."""
    return os.getenv("API_TOKEN")


async def verify_token(x_api_token: str = Header(..., description="API authentication token")):
    """
    Verify API token from request header.
    
    Args:
        x_api_token: Token from X-API-Token header
        
    Raises:
        HTTPException: If token is missing, invalid, or doesn't match
        
    Returns:
        str: The validated token
    """
    expected_token = get_api_token()
    
    # If no token is configured, skip authentication (development mode)
    if not expected_token:
        return None
    
    # Check if token matches
    if x_api_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return x_api_token
