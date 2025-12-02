import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from config.dependecies_services import get_user_service
from service.user_service import UserService
from api.auth import verify_admin

router = APIRouter(prefix="/users", tags=["users"])

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(user: UserLogin,
             region: str,
    service: UserService = Depends(get_user_service)):
    """
    Registra un nuovo utente normale (non admin).
    """
    try:
        new_user = service.new_user(user.email, user.password, region, is_admin=False)
        return {
            "message": "User registered successfully", 
            "user_id": str(new_user.id),
            "is_admin": new_user.is_admin
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/register_admin")
def register_admin(
    user: UserLogin,
    region: str,
    service: UserService = Depends(get_user_service),
    admin_user_id: uuid.UUID = Depends(verify_admin)
):
    """
    Registra un nuovo utente amministratore.
    Richiede privilegi di amministratore per creare altri admin.
    """
    try:
        new_user = service.new_user(user.email, user.password, region, is_admin=True)
        return {
            "message": "Admin user registered successfully", 
            "user_id": str(new_user.id),
            "is_admin": new_user.is_admin
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login")
def login(user: UserLogin,
    service: UserService = Depends(get_user_service)):
    """
    Login utente. Restituisce user_id e is_admin.
    """
    auth_user = service.get_user(user.email, user.password)
    if not auth_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {
        "message": "Login successful", 
        "user_id": str(auth_user.id),
        "is_admin": auth_user.is_admin
    }

@router.post("/confirm")
def confirm_user(user: UserLogin,
    service: UserService = Depends(get_user_service)):
    confirmed = service.confirm_user(user.email, user.password)
    if confirmed:
        return {"message": "User confirmed"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or invalid credentials")
