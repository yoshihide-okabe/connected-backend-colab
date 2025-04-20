# app/api/users/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 相対インポートに変更
from ...core.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # パスワード (ハッシュ化されたもの)
    category_id = Column(String, nullable=True)  # カンマ区切りのカテゴリー
    point_total = Column(Integer, default=0)  # ポイント合計
    num_answer = Column(Integer, default=0)  # 回答数
    last_login_at = Column(DateTime, nullable=True)  # 最終ログイン日時
    
    # リレーションシップ
    projects = relationship("CoCreationProject", back_populates="creator", foreign_keys="CoCreationProject.creator_user_id")
    favorite_projects = relationship("UserProjectFavorite", back_populates="user")
    participating_projects = relationship("UserProjectParticipation", back_populates="user")
    messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_user_id")  # userからsenderに変更
    troubles = relationship("Trouble", back_populates="creator")
    
    def get_points(self):
        """ポイント取得メソッド"""
        return self.point_total or 0
    
    def get_category_id(self):
        """カテゴリーIDを取得"""
        if not self.category_id:
            return None
        try:
            return int(self.category_id)
        except (ValueError, TypeError):
            return None
    
    def get_category_name(self, db):
        """カテゴリー名を取得（DBセッションが必要）"""
        if not self.category_id:
            return None
        
        from ..projects.models import ProjectCategory  # 循環インポートを避けるためここでインポート
        
        try:
            category_id = int(self.category_id)
            category = db.query(ProjectCategory).filter(ProjectCategory.category_id == category_id).first()
            return category.name if category else None
        except (ValueError, TypeError, AttributeError):
            return None
    
    def set_category_id(self, category_id):
        """カテゴリーIDを設定"""
        if category_id is None:
            self.category_id = None
        else:
            try:
                self.category_id = str(int(category_id))  # 整数に変換して文字列として保存
            except (ValueError, TypeError):
                self.category_id = None
