# app/api/users/schemas.py
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ...schemas.base import BaseSchemaModel

class UserBase(BaseSchemaModel):
    name: str = Field(..., min_length=1, max_length=50, description="ユーザー名")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="パスワード")
    confirm_password: str = Field(..., description="確認用パスワード")
    category_id: Optional[int] = Field(None, description="ユーザーの興味/専門カテゴリー")

class UserUpdate(BaseSchemaModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="ユーザー名")
    password: Optional[str] = Field(None, min_length=8, description="パスワード")
    confirm_password: Optional[str] = Field(None, description="確認用パスワード")
    category_id: Optional[int] = Field(None, description="ユーザーの興味/専門カテゴリー")

class UserResponse(UserBase):
    id: int
    category_id: Optional[int] = None
    category_name: Optional[str] = None  # カテゴリー名を追加
    points: int = 0
    last_login_at: Optional[datetime] = None  # 名前を合わせる
    
class UserLogin(BaseSchemaModel):
    name: str
    password: str

class Token(BaseSchemaModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    user_name: str

class TokenData(BaseSchemaModel):
    user_id: Optional[int] = None
