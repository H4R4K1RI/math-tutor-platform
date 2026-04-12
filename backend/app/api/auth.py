from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.dependencies import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["authentication"])
limiter = Limiter(key_func=get_remote_address)

@router.get("/test-db")
async def test_db(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        return {"status": "success", "result": value}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role="student",
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Вход в систему, устанавливает HttpOnly cookie с токеном"""
    
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )
    
    # Создаём токен
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role
    }
    access_token = create_access_token(token_data)
    
    # Устанавливаем HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # True только при HTTPS
        samesite="lax",
        max_age=30 * 60,  # 30 минут
        path="/"
    )
    
    return {"message": "Login successful"}

@router.post("/logout")
async def logout(response: Response):
    """Выход из системы — удаляем cookie"""
    response.delete_cookie("access_token", path="/")
    return {"message": "Logout successful"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user
