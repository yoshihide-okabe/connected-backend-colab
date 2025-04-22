# app/api/projects/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

from ...schemas.base import BaseSchemaModel

class CategoryBase(BaseSchemaModel):
    name: str = Field(..., min_length=1, description="カテゴリー名")

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    category_id: int

class ProjectBase(BaseSchemaModel):
    title: str = Field(..., min_length=1, description="プロジェクトのタイトル")
    description: str = Field(..., min_length=10, description="プロジェクトの詳細説明")
    summary: Optional[str] = Field(None, description="プロジェクトの概要")
    category_id: Optional[int] = Field(None, description="プロジェクトのカテゴリーID")

class ProjectCreate(ProjectBase):
    creator_user_id: int

class ProjectUpdate(BaseSchemaModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=10)
    summary: Optional[str] = Field(None)
    category_id: Optional[int] = Field(None)

class ProjectResponse(BaseSchemaModel):
    project_id: int
    title: str
    description: str
    summary: Optional[str] = None
    creator_user_id: int
    creator_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    likes: int = 0
    comments: int = 0
    is_favorite: bool = False
    category_id: Optional[int] = None
    category: Optional[CategoryResponse] = None
    
    # フロントエンド互換のプロパティ (model_config設定により自動追加される)
    @property
    def id(self) -> int:
        return self.project_id
        
    @property
    def owner_name(self) -> str:
        return self.creator_name
        
    @property
    def status(self) -> str:
        return "active"
        
    @property
    def isFavorite(self) -> bool:
        return self.is_favorite

class ProjectListResponse(BaseSchemaModel):
    new_projects: List[ProjectResponse]
    favorite_projects: List[ProjectResponse]
    liked_projects: List[ProjectResponse]  # いいねしたプロジェクトを追加
    total_projects: int

class UserProjectFavoriteCreate(BaseSchemaModel):
    user_id: int
    project_id: int

class RankingUser(BaseSchemaModel):
    name: str
    points: int
    rank: int
