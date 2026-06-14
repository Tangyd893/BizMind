from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.services.auth_service import _user_to_response, login, register
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register_user(
    req: RegisterRequest, session: AsyncSession = Depends(get_db)
) -> AuthResponse:
    return await register(session, req)


@router.post("/login", response_model=AuthResponse)
async def login_user(
    req: LoginRequest, session: AsyncSession = Depends(get_db)
) -> AuthResponse:
    return await login(session, req)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return _user_to_response(user)
