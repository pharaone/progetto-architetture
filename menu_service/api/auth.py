"""
Sistema di autenticazione e autorizzazione per il menu service.
"""
import uuid
from fastapi import Header, HTTPException, Depends, status
from sqlalchemy.orm import Session

from config.dependecies_configuration import get_db
from repository.user_repository import UserRepository


def get_current_user_id(x_user_id: str = Header(..., description="User ID from login")) -> uuid.UUID:
    """
    Estrae l'ID utente dall'header X-User-Id.
    Questo header dovrebbe essere impostato dal client dopo il login.
    """
    try:
        return uuid.UUID(x_user_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-User-Id header"
        )


def verify_admin(
    x_user_id: str = Header(..., description="User ID from login"),
    db: Session = Depends(get_db)
) -> uuid.UUID:
    """
    Verifica che l'utente corrente sia un amministratore.
    Solleva un'eccezione se l'utente non è admin.
    """
    try:
        user_id = uuid.UUID(x_user_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-User-Id header"
        )
    
    # Verifica che l'utente esista e sia admin
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return user_id

