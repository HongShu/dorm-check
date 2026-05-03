from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    name: str
    assigned_building: int | None = None


class ApiResponse(BaseModel):
    code: int = 0
    data: dict | list | None = None
    message: str = "ok"
