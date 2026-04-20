from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_current_user
from app.core.email import generate_verification_token, send_verification_email, verify_email_token
from fastapi.responses import HTMLResponse

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["authentication"])

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
    # Проверяем, существует ли пользователь
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )
    
    # Создаём нового пользователя
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role="student",
        is_active=True,
        is_verified=False
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Отправляем письмо с подтверждением
    verification_token = generate_verification_token(user_data.email)
    await send_verification_email(user_data.email, verification_token)
    
    return new_user

@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Аккаунт пользователя отключён"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email не подтверждён. Проверьте почту и перейдите по ссылке"
        )
    
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role
    }
    access_token = create_access_token(token_data)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 60,
        path="/"
    )
    
    return {"message": "Вход выполнен успешно"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"message": "Выход выполнен успешно"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    email = verify_email_token(token)
    
    if not email:
        return """
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Ошибка подтверждения</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <div style="max-width: 500px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="font-size: 60px;">❌</div>
                <h2 style="color: #e74c3c;">Ошибка подтверждения</h2>
                <p style="color: #555;">Недействительная или просроченная ссылка</p>
                <a href="/login" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background: #2e7d5e; color: white; text-decoration: none; border-radius: 8px;">Перейти ко входу</a>
            </div>
        </body>
        </html>
        """
    
    # Обновляем статус пользователя
    await db.execute(
        update(User).where(User.email == email).values(is_verified=True)
    )
    await db.commit()
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="3;url=/login">
        <title>Email подтверждён</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #f5f5f0 0%, #e8f0ea 100%);
                margin: 0;
                padding: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .card {
                max-width: 500px;
                margin: 20px;
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                text-align: center;
            }

            h1 {
                color: #2e7d5e;
                margin-bottom: 15px;
            }
            p {
                color: #555;
                line-height: 1.6;
                margin-bottom: 25px;
            }
            .redirect {
                font-size: 14px;
                color: #888;
            }
            .btn {
                display: inline-block;
                margin-top: 20px;
                padding: 10px 24px;
                background: #2e7d5e;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #1e5a44;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Email подтверждён!</h1>
            <p>Ваш email успешно подтверждён. Спасибо за регистрацию!</p>
            <p class="redirect">Перенаправление на страницу входа через 3 секунды...</p>
            <a href="/login" class="btn">Перейти сейчас</a>
        </div>
        <script>
            setTimeout(function() {
                window.location.href = '/login';
            }, 3000);
        </script>
    </body>
    </html>
    """
