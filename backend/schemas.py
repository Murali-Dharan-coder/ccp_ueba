from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    employee_id: str
    email: str
    name: str
    department: str

class UserCreate(UserBase):
    password: str
    status: Optional[str] = "Active"
    anomaly_score: Optional[float] = 0.0
    critical_level: Optional[str] = "Low"

class UserResponse(UserBase):
    id: int
    anomaly_score: float
    critical_level: str
    status: str
    lock_reason: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    employee_id_or_email: str
    password: str

class AdminLoginRequest(BaseModel):
    pin: str

class LockUserRequest(BaseModel):
    reason: str
