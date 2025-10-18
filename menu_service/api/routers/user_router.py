from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from config.dependecies_services import get_user_service
from service.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(user: UserLogin,
    service: UserService = Depends(get_user_service)):
    try:
        service.new_user(user.email, user.password)
        return {"message": "User registered successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login")
def login(user: UserLogin,
    service: UserService = Depends(get_user_service)):
    auth_user = service.get_user(user.email, user.password)
    if not auth_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"message": "Login successful"}

@router.post("/confirm")
def confirm_user(user: UserLogin,
    service: UserService = Depends(get_user_service)):
    confirmed = service.confirm_user(user.email, user.password)
    if confirmed:
        return {"message": "User confirmed"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or invalid credentials")
