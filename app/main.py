# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os
from pathlib import Path

# デフォルトユーザー作成用の追加
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# コアの設定をインポート
from core.config import settings

# 認証関連のインポートを追加
from api.users.schemas import Token
from api.auth.router import login_for_access_token

# APIルーターのインポート
from api.troubles.router import router as troubles_router
from api.projects.router import router as projects_router
from api.users.router import router as users_router
from api.messages.router import router as messages_router
from api.auth.router import router as auth_router

try:
    from app.api.troubles.categories import router as trouble_categories_router
    from app.api.projects.categories import router as project_categories_router
    has_categories = True
except ImportError as e:
    print(f"カテゴリーモジュールのインポートに失敗しました: {e}")
    has_categories = False

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="コラボゲームズのバックエンドAPIサービス",
    version="0.1.0"
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの追加
app.include_router(troubles_router, prefix=f"{settings.API_V1_STR}/troubles", tags=["troubles"])
app.include_router(projects_router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(messages_router, prefix=f"{settings.API_V1_STR}/messages", tags=["messages"])
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
# カテゴリールーターを追加
app.include_router(trouble_categories_router, prefix=f"{settings.API_V1_STR}/trouble-categories", tags=["trouble-categories"])
app.include_router(project_categories_router, prefix=f"{settings.API_V1_STR}/project-categories", tags=["project-categories"])

# ルートレベルに /token エンドポイントを追加
app.post("/token", response_model=Token)(login_for_access_token)

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        reload=settings.DEBUG
    )


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化処理"""
    # ↓↓↓ 追加：環境変数と接続設定のログ出力 ↓↓↓
    print("\n===== DATABASE CONNECTION SETTINGS =====")
    print(f"USE_AZURE: {settings.USE_AZURE} (type: {type(settings.USE_AZURE)})")
    print(f"DATABASE_URL: {settings.SQLALCHEMY_DATABASE_URL}")
    if settings.USE_AZURE:
        print(f"AZURE_MYSQL_HOST: {settings.AZURE_MYSQL_HOST}")
        print(f"AZURE_MYSQL_DATABASE: {settings.AZURE_MYSQL_DATABASE}")
        print(f"AZURE_MYSQL_USER: {settings.AZURE_MYSQL_USER}")
        print(f"AZURE_MYSQL_PORT: {settings.AZURE_MYSQL_PORT}")
        print(f"AZURE_MYSQL_SSL_MODE: {settings.AZURE_MYSQL_SSL_MODE}")
    else:
        print(f"DB_HOST: {settings.DB_HOST}")
        print(f"DB_NAME: {settings.DB_NAME}")
    print("========================================\n")
    
    from app.core.database import SessionLocal
    from app.api.users.models import User
    from app.core.security import get_password_hash
    
    # ↓↓↓ 追加：セッション作成のログ出力 ↓↓↓
    print("データベースセッションを初期化します...")
    # ↑↑↑ 追加ここまで ↑↑↑

    db = SessionLocal()
    try:
        # デフォルトユーザーの確認
        default_user = db.query(User).filter(User.user_id == 1).first()
        if not default_user:
            print("デフォルトユーザーが存在しません。作成します...")
            # デフォルトユーザーの作成
            default_user = User(
                user_id=1,
                name="admin",
                password=get_password_hash("admin123"),
                categories="システム部",
                point_total=1000,
                created_at=datetime.utcnow(),
                last_login_at=datetime.utcnow()
            )
            db.add(default_user)
            db.commit()
            print("デフォルトユーザーを作成しました: ID=1, name=admin")
    except SQLAlchemyError as e:
        db.rollback()
        # ↓↓↓ 修正：エラーログの詳細化 ↓↓↓
        print(f"デフォルトユーザー作成エラー: {str(e)}")
        print("SQLAlchemy エラーの詳細:")
        import traceback
        traceback.print_exc()
        # ↑↑↑ 修正ここまで ↑↑↑
    except Exception as e:
        # ↓↓↓ 追加：その他のエラーをキャッチして詳細表示 ↓↓↓
        print(f"予期せぬエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        # ↑↑↑ 追加ここまで ↑↑↑
    finally:
        db.close()
        # ↓↓↓ 追加：デバッグ情報 ↓↓↓
        print("データベースセッションを終了しました")
        # ↑↑↑ 追加ここまで ↑↑↑

# ミドルウェア追加: すべてのリクエストヘッダーをログ出力
@app.middleware("http")
async def log_requests(request, call_next):
    """リクエストヘッダーをログ出力するミドルウェア"""
    print(f"Request path: {request.url.path}")
    print(f"Request headers: {request.headers}")
    
    # ↓↓↓ 追加：レスポンスと例外のキャッチ ↓↓↓
    try:
        response = await call_next(request)
        print(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        print(f"Request processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    # ↑↑↑ 修正ここまで ↑↑↑