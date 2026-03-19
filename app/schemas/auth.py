from typing import Optional

from pydantic import BaseModel, EmailStr


class MagicLinkRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class MagicLinkResponse(BaseModel):
    message: str
    access_token: Optional[str] = None
    user_id: Optional[str] = None
    is_new_user: Optional[bool] = None
    onboarding_done: Optional[bool] = None
    role: Optional[str] = None


class VerifyTokenRequest(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    is_new_user: bool
    onboarding_done: bool
    role: str = "learner"
