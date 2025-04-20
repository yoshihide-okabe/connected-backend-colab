# app/api/projects/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query  # Queryを追加

from ...core.database import get_db
from ..auth.jwt import get_current_user
# from ...core.dependencies import get_current_user
from ..users.models import User
from .models import CoCreationProject, UserProjectFavorite, ProjectCategory
from .schemas import (
    ProjectResponse, 
    ProjectListResponse, 
    ProjectCreate, 
    ProjectUpdate,
    CategoryResponse,
    RankingUser
)

router = APIRouter()

@router.get("/user", response_model=List[ProjectResponse])
def get_user_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """現在のユーザーが作成したプロジェクトのみを取得する"""
    user_id = current_user.user_id
    
    # ユーザーが作成したプロジェクトを取得
    user_projects = (
        db.query(CoCreationProject)
        .filter(CoCreationProject.creator_user_id == user_id)
        .order_by(CoCreationProject.created_at.desc())
        .all()
    )

    # プロジェクトをレスポンススキーマに変換
    result = []
    for project in user_projects:
        # お気に入り判定
        is_favorite = db.query(UserProjectFavorite).filter(
            UserProjectFavorite.user_id == user_id,
            UserProjectFavorite.project_id == project.project_id
        ).first() is not None

        # プロジェクト作成者の情報取得
        creator = db.query(User).filter(User.user_id == project.creator_user_id).first()

        # カテゴリー情報の取得
        category = None
        if hasattr(project, 'category_id') and project.category_id:
            category = db.query(ProjectCategory).filter(
                ProjectCategory.category_id == project.category_id
            ).first()

        # ダミーのいいね数とコメント数
        likes = 24  # TODO: 実際のロジックに置き換える
        comments = 8  # TODO: 実際のロジックに置き換える

        result.append(ProjectResponse(
            project_id=project.project_id,
            title=project.title,
            summary=project.summary if hasattr(project, 'summary') else None,
            description=project.description,
            creator_user_id=project.creator_user_id,
            creator_name=creator.name if creator else "不明",
            created_at=project.created_at,
            updated_at=project.updated_at if hasattr(project, 'updated_at') else None,
            likes=likes,
            comments=comments,
            is_favorite=is_favorite,
            category_id=project.category_id if hasattr(project, 'category_id') else None,
            category=CategoryResponse(
                category_id=category.category_id,
                name=category.name
            ) if category else None
        ))
    
    return result

@router.get("/", response_model=ProjectListResponse)
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.user_id
    
    # 新着プロジェクト
    new_projects = (
        db.query(CoCreationProject)
        .order_by(CoCreationProject.created_at.desc())
        .limit(8)
        .all()
    )

    # お気に入りプロジェクト
    favorite_projects = (
        db.query(CoCreationProject)
        .join(UserProjectFavorite)
        .filter(UserProjectFavorite.user_id == user_id)
        .order_by(CoCreationProject.created_at.desc())
        .limit(8)
        .all()
    )

    # プロジェクト総数
    total_projects = db.query(CoCreationProject).count()

    # プロジェクトをレスポンススキーマに変換
    def convert_project(project):
        # ダミーのいいね数とコメント数
        likes = 24  # TODO: 実際のロジックに置き換える
        comments = 8  # TODO: 実際のロジックに置き換える
        
        # お気に入り判定
        is_favorite = db.query(UserProjectFavorite).filter(
            UserProjectFavorite.user_id == user_id,
            UserProjectFavorite.project_id == project.project_id
        ).first() is not None

        # プロジェクト作成者の情報取得
        creator = db.query(User).filter(User.user_id == project.creator_user_id).first()

        # カテゴリー情報の取得
        category = None
        if hasattr(project, 'category_id') and project.category_id:
            category = db.query(ProjectCategory).filter(
                ProjectCategory.category_id == project.category_id
            ).first()

        return {
        "project_id": project.project_id,
        "id": project.project_id,  # フロントエンド互換のために追加
        "title": project.title,
        "description": project.description,
        "summary": project.summary if hasattr(project, 'summary') else None,
        "creator_user_id": project.creator_user_id,
        "creator_name": creator.name if creator else "不明",
        "owner_name": creator.name if creator else "不明",  # フロントエンド互換のために追加
        "status": "active",  # フロントエンド側が期待する形式
        "category_name": category.name if category else "その他",  # フロントエンド互換の名前
        "created_at": project.created_at,
        "createdAt": project.created_at.isoformat() if project.created_at else None,  # フロントエンド互換
        "updated_at": project.updated_at if hasattr(project, 'updated_at') else None,
        "likes": likes,
        "comments": comments,
        "is_favorite": is_favorite,
        "isFavorite": is_favorite,  # フロントエンド互換のために追加
        "category_id": project.category_id if hasattr(project, 'category_id') else None,
        "category": {
            "category_id": category.category_id,
            "name": category.name
        } if category else None
    }

    return ProjectListResponse(
        new_projects=[convert_project(p) for p in new_projects],
        favorite_projects=[convert_project(p) for p in favorite_projects],
        total_projects=total_projects
    )

@router.get("/categories", response_model=List[CategoryResponse])
def get_project_categories(db: Session = Depends(get_db)):
    # データベースからカテゴリを取得
    categories = db.query(ProjectCategory).all()
    
    # カテゴリがない場合は初期データを挿入
    if not categories:
        default_categories = [
            "テクノロジー", "デザイン", "マーケティング", "ビジネス", 
            "教育", "コミュニティ", "医療", "環境"
        ]
        
        for name in default_categories:
            category = ProjectCategory(name=name)
            db.add(category)
        
        db.commit()
        categories = db.query(ProjectCategory).all()
    
    return [
        CategoryResponse(
            category_id=category.category_id,
            name=category.name
        ) for category in categories
    ]

@router.get("/ranking", response_model=List[RankingUser])
def get_activity_ranking(db: Session = Depends(get_db)):
    # TODO: 実際のポイント計算ロジックに置き換える
    # 現時点では、ダミーデータを返す
    ranking_data = [
        RankingUser(name="キツネ", points=1250, rank=1),
        RankingUser(name="パンダ", points=980, rank=2),
        RankingUser(name="ウサギ", points=875, rank=3)
    ]
    return ranking_data

@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # プロジェクト作成のバリデーション
    if not project.title or not project.description:
        raise HTTPException(status_code=400, detail="必須項目を入力してください")

    # 自分以外のユーザーIDでプロジェクトを作成できないようにする
    if project.creator_user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, 
            detail="自分以外のユーザーIDでプロジェクトを作成することはできません"
        )

    # カテゴリーが指定されている場合は存在確認
    if hasattr(project, 'category_id') and project.category_id:
        category = db.query(ProjectCategory).filter(
            ProjectCategory.category_id == project.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=404,
                detail="指定されたカテゴリーが見つかりません"
            )

    # プロジェクトを作成
    new_project = CoCreationProject(
        title=project.title,
        summary=project.summary,
        description=project.description,
        creator_user_id=current_user.user_id,
        created_at=datetime.now(),
        category_id=project.category_id if hasattr(project, 'category_id') else None
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return {
        "message": "プロジェクトを登録しました", 
        "project_id": new_project.project_id
    }

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    # プロジェクトの詳細を取得
    project = db.query(CoCreationProject).filter(CoCreationProject.project_id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
    
    # TODO: いいね数とコメント数の実装
    likes = 24  # 仮の値
    comments = 8  # 仮の値
    
    # お気に入り判定
    is_favorite = False
    if current_user:
        is_favorite = db.query(UserProjectFavorite).filter(
            UserProjectFavorite.user_id == current_user.user_id,
            UserProjectFavorite.project_id == project_id
        ).first() is not None
    
    # プロジェクト作成者の情報取得
    creator = db.query(User).filter(User.user_id == project.creator_user_id).first()
    
    # カテゴリー情報の取得
    category = None
    if hasattr(project, 'category_id') and project.category_id:
        category = db.query(ProjectCategory).filter(
            ProjectCategory.category_id == project.category_id
        ).first()
    
    return ProjectResponse(
        project_id=project.project_id,
        title=project.title,
        summary=project.summary,
        description=project.description,
        creator_user_id=project.creator_user_id,
        creator_name=creator.name if creator else "不明",
        created_at=project.created_at,
        updated_at=project.updated_at,
        likes=likes,
        comments=comments,
        is_favorite=is_favorite,
        category_id=project.category_id if hasattr(project, 'category_id') else None,
        category=CategoryResponse(
            category_id=category.category_id,
            name=category.name
        ) if category else None
    )

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """プロジェクトを更新"""
    db_project = db.query(CoCreationProject).filter(CoCreationProject.project_id == project_id).first()
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プロジェクトが見つかりません"
        )
    
    # プロジェクトの所有者のみが更新可能
    if db_project.creator_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このプロジェクトを更新する権限がありません"
        )
    
    # カテゴリーが指定されている場合は存在確認
    if hasattr(project_update, 'category_id') and project_update.category_id:
        category = db.query(ProjectCategory).filter(
            ProjectCategory.category_id == project_update.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=404,
                detail="指定されたカテゴリーが見つかりません"
            )
    
    # 更新データを適用
    update_data = project_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_project, key, value)
    
    # 更新日時を設定
    db_project.updated_at = datetime.now()
    
    db.commit()
    db.refresh(db_project)
    
    # プロジェクト作成者の情報取得
    creator = db.query(User).filter(User.user_id == db_project.creator_user_id).first()
    
    # カテゴリー情報の取得
    category = None
    if hasattr(db_project, 'category_id') and db_project.category_id:
        category = db.query(ProjectCategory).filter(
            ProjectCategory.category_id == db_project.category_id
        ).first()
    
    return ProjectResponse(
        project_id=db_project.project_id,
        title=db_project.title,
        summary=db_project.summary,
        description=db_project.description,
        creator_user_id=db_project.creator_user_id,
        creator_name=creator.name if creator else "不明",
        created_at=db_project.created_at,
        updated_at=db_project.updated_at,
        likes=24,  # 仮の値
        comments=8,  # 仮の値
        is_favorite=False,  # 更新後のお気に入り状態は別途取得必要
        category_id=db_project.category_id if hasattr(db_project, 'category_id') else None,
        category=CategoryResponse(
            category_id=category.category_id,
            name=category.name
        ) if category else None
    )
    
# --- 以下、新規追加のエンドポイント ---

# 新着プロジェクト取得 API（新規追加）
@router.get("/recent", response_model=List[ProjectResponse])
def get_recent_projects(
    limit: int = Query(5, ge=1, le=100, description="取得するプロジェクト数の上限（1〜100）"),
    hours: int = Query(24, ge=1, le=720, description="何時間前までのプロジェクトを「新着」とするか（1〜720時間）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    指定された時間内の新着プロジェクトを取得する
    """
    # 現在時刻からhours時間前の日時を計算
    since_time = datetime.now() - timedelta(hours=hours)
    
    # 新着プロジェクトを取得
    recent_projects = (
        db.query(CoCreationProject)
        .filter(CoCreationProject.created_at >= since_time)
        .order_by(CoCreationProject.created_at.desc())
        .limit(limit)
        .all()
    )
    
    # プロジェクトをレスポンススキーマに変換
    result = []
    for project in recent_projects:
        # お気に入り判定
        is_favorite = db.query(UserProjectFavorite).filter(
            UserProjectFavorite.user_id == current_user.user_id,
            UserProjectFavorite.project_id == project.project_id
        ).first() is not None
        
        # プロジェクト作成者の情報取得
        creator = db.query(User).filter(User.user_id == project.creator_user_id).first()
        
        # カテゴリー情報の取得
        category = None
        if hasattr(project, 'category_id') and project.category_id:
            category = db.query(ProjectCategory).filter(
                ProjectCategory.category_id == project.category_id
            ).first()
        
        # ダミーのいいね数とコメント数
        likes = 24  # ダミー値
        comments = 8  # ダミー値
        
        result.append(ProjectResponse(
            project_id=project.project_id,
            title=project.title,
            summary=project.summary if hasattr(project, 'summary') else None,
            description=project.description,
            creator_user_id=project.creator_user_id,
            creator_name=creator.name if creator else "不明",
            created_at=project.created_at,
            updated_at=project.updated_at if hasattr(project, 'updated_at') else None,
            likes=likes,
            comments=comments,
            is_favorite=is_favorite,
            category_id=project.category_id if hasattr(project, 'category_id') else None,
            category=CategoryResponse(
                category_id=category.category_id,
                name=category.name
            ) if category else None
        ))
    
    return result

# お気に入りプロジェクト取得 API（新規追加）
@router.get("/favorites", response_model=List[ProjectResponse])
def get_favorite_projects(
    limit: int = Query(5, ge=1, le=100, description="取得するプロジェクト数の上限（1〜100）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    現在のユーザーのお気に入りプロジェクトを取得する
    """
    # お気に入りプロジェクトを取得
    favorite_projects = (
        db.query(CoCreationProject)
        .join(UserProjectFavorite, UserProjectFavorite.project_id == CoCreationProject.project_id)
        .filter(UserProjectFavorite.user_id == current_user.user_id)
        .order_by(CoCreationProject.created_at.desc())
        .limit(limit)
        .all()
    )
    
    # プロジェクトをレスポンススキーマに変換
    result = []
    for project in favorite_projects:
        # プロジェクト作成者の情報取得
        creator = db.query(User).filter(User.user_id == project.creator_user_id).first()
        
        # カテゴリー情報の取得
        category = None
        if hasattr(project, 'category_id') and project.category_id:
            category = db.query(ProjectCategory).filter(
                ProjectCategory.category_id == project.category_id
            ).first()
        
        # ダミーのいいね数とコメント数
        likes = 24  # ダミー値
        comments = 8  # ダミー値
        
        # ここでProjectResponseインスタンスを作成
        project_response = ProjectResponse(
            project_id=project.project_id,
            title=project.title,
            summary=project.summary if hasattr(project, 'summary') else None,
            description=project.description,
            creator_user_id=project.creator_user_id,
            creator_name=creator.name if creator else "不明",
            created_at=project.created_at,
            updated_at=project.updated_at if hasattr(project, 'updated_at') else None,
            likes=likes,
            comments=comments,
            is_favorite=True,  # お気に入りリストなので常にTrue
            category_id=project.category_id if hasattr(project, 'category_id') else None,
            category=CategoryResponse(
                category_id=category.category_id,
                name=category.name
            ) if category else None
        )
        
        result.append(project_response)
    
    return result

# お気に入り追加 API（新規追加）
@router.post("/{project_id}/favorite", status_code=status.HTTP_201_CREATED)
def add_project_to_favorites(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    プロジェクトをお気に入りに追加
    """
    # プロジェクトの存在確認
    project = db.query(CoCreationProject).filter(
        CoCreationProject.project_id == project_id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プロジェクトが見つかりません"
        )
    
    # すでにお気に入りに追加されているか確認
    existing_favorite = db.query(UserProjectFavorite).filter(
        UserProjectFavorite.user_id == current_user.user_id,
        UserProjectFavorite.project_id == project_id
    ).first()
    
    if existing_favorite:
        # すでに追加済みの場合は成功として返す
        return {
            "message": "プロジェクトはすでにお気に入りに追加されています",
            "project_id": project_id,
            "is_favorite": True
        }
    
    # お気に入り追加
    new_favorite = UserProjectFavorite(
        user_id=current_user.user_id,
        project_id=project_id
    )
    
    db.add(new_favorite)
    db.commit()
    
    return {
        "message": "プロジェクトをお気に入りに追加しました",
        "project_id": project_id,
        "is_favorite": True
    }

# お気に入り削除 API（新規追加）
@router.delete("/{project_id}/favorite", status_code=status.HTTP_200_OK)
def remove_project_from_favorites(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    プロジェクトをお気に入りから削除
    """
    # お気に入りレコードを取得
    favorite = db.query(UserProjectFavorite).filter(
        UserProjectFavorite.user_id == current_user.user_id,
        UserProjectFavorite.project_id == project_id
    ).first()
    
    if not favorite:
        # すでに削除されている場合も成功として返す
        return {
            "message": "プロジェクトはお気に入りに追加されていません",
            "project_id": project_id,
            "is_favorite": False
        }
    
    # お気に入りから削除
    db.delete(favorite)
    db.commit()
    
    return {
        "message": "プロジェクトをお気に入りから削除しました",
        "project_id": project_id,
        "is_favorite": False
    }