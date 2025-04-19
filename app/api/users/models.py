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
    messages = relationship("Message", back_populates="user")
    troubles = relationship("Trouble", back_populates="creator")
    
    def get_points(self):
        """ポイント取得メソッド"""
        return self.point_total or 0
    
    def get_categories_list(self):
        """カテゴリー文字列をリストに変換"""
        if not self.category_id:
            return []
        # 単一のカテゴリーIDを配列に変換
        return [str(self.category_id)]
    
    def set_categories_list(self, categories_list):
        """カテゴリーリストを文字列に変換"""
        if not categories_list:
            self.category_id = None
        else:
            # 最初のカテゴリーのみ使用
            try:
                self.category_id = int(categories_list[0])
            except (ValueError, IndexError):
                self.category_id = None