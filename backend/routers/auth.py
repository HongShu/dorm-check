from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from jose import jwt

from database import get_db
from config import settings
from models.user import User
from schemas.auth import LoginRequest, LoginResponse, ApiResponse

router = APIRouter(prefix="/api/auth", tags=["认证"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


@router.post("/login", response_model=ApiResponse)
def login(body: LoginRequest, db=Depends(get_db)):
    user = db.get(User, body.username)
    if not user or not verify_password(body.password, user.password_hash):
        return ApiResponse(code=4001, data=None, message="登录失败：密码错误")

    token = create_token(user.username, user.role)
    data = {
        "token": token,
        "role": user.role,
        "name": user.name,
        "assigned_building": user.assigned_building,
    }
    return ApiResponse(data=data)


@router.post("/logout", response_model=ApiResponse)
def logout():
    return ApiResponse(data=None)


def get_current_user(token: str = None) -> User:
    """从 token 解析当前用户（从 Header Authorization: Bearer <token> 提取）"""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except Exception:
        return None
