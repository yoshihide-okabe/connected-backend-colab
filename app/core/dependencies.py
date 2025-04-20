import os
import sys
from pathlib import Path
from typing import Optional  # Optional をインポート
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

# プロジェクトルートをPythonパスに追加
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 相対インポートに変更
from .database import get_db
from .config import settings
# アプリケーションのモジュールをインポート
from app.api.users.models import User
from app.api.users.schemas import TokenData

# async def get_current_user(
#     db: Session = Depends(get_db),
#     user_id: Optional[int] = None  # ヘッダーやクエリパラメータから取得することも可能
# ) -> User:
#     """
#     指定されたユーザーIDのユーザーを返す
#     指定がない場合はデフォルトでID=1を返す
#     """
#     try:
#         # ユーザーIDが指定されていない場合はデフォルト値を使用
#         target_user_id = user_id if user_id is not None else 1
#         
#         # ユーザーを取得
#         user = db.query(User).filter(User.user_id == target_user_id).first()
#         
#         if not user:
#             # 指定されたユーザーが見つからない場合はデフォルトユーザーを試す
#             if target_user_id != 1:
#                 user = db.query(User).filter(User.user_id == 1).first()
#             
#             # それでも見つからない場合はエラー
#             if not user:
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail=f"ユーザーID={target_user_id}が見つかりません。"
#                 )
#         
#         return user
#     except Exception as e:
#         import traceback
#         print(f"認証エラー: {str(e)}")
#         traceback.print_exc()
#         
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"認証処理中にエラーが発生しました: {str(e)}"
#         )
        
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    現在のユーザーを取得する依存関係
    
    :param token: アクセストークン
    :param db: データベースセッション
    :return: 現在のユーザー
    :raises: 認証エラーの場合はHTTPException
    """
    # 開発環境では認証をスキップすることもできる
    if settings.DEBUG and "FAKE_AUTH" in os.environ and os.environ["FAKE_AUTH"] == "True":
        # デフォルトユーザーを返す（ID=1のユーザーを想定）
        default_user = db.query(User).filter(User.user_id == 1).first()
        if default_user:
            return default_user
        
        # デフォルトユーザーが存在しない場合はエラー
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="開発環境用のデフォルトユーザー（ID=1）が見つかりません。データベースにユーザーを作成してください。",
        )

    # 通常の認証処理
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報が無効です",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    try:
        # JWTトークンからペイロードを取得
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
        # 文字列として受け取った場合は整数に変換
        if isinstance(user_id, str):
            user_id = int(user_id)
            
        token_data = TokenData(user_id=user_id)
    except (JWTError, ValueError):
        # JWTエラーまたは整数変換エラー
        raise credentials_exception
    
    # ユーザーIDからユーザーを検索
    user = db.query(User).filter(User.user_id == token_data.user_id).first()
    
    if user is None:
        raise credentials_exception
    
    return user