"""
Authentication endpoints
"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.db.deps import get_db
from app.schemas.auth import Token

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests."""
    # TODO: Implement user authentication against database
    # For now, simple hardcoded authentication for development
    if form_data.username == "admin" and form_data.password == "admin":
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            form_data.username, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/test-token")
async def test_token(current_user: str = Depends(get_current_user)) -> Any:
    """Test access token."""
    return {"message": f"Hello {current_user}"}


# Import here to avoid circular imports
from app.db.deps import get_current_user