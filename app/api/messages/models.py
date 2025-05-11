# app/api/messages/models.py
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 相対インポートに変更
from ...core.database import Base

class Message(Base):
    __tablename__ = "trouble_messages"

    message_id = Column(Integer, primary_key=True, index=True)
    trouble_id = Column(Integer, ForeignKey("troubles.trouble_id"), nullable=False)
    sender_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    parent_message_id = Column(Integer, ForeignKey("trouble_messages.message_id"), nullable=True) 
    
    # リレーションシップ
    sender = relationship("User", back_populates="messages")
    trouble = relationship("Trouble", back_populates="messages")
    
    # 自己参照リレーションシップを一時的に無効化
    # remote_sideパラメータを明示的に指定
    # replies = relationship(
    #     "Message", 
    #     backref="parent", 
    #     remote_side=[message_id]
    # )
    
    # 代わりにget_repliesメソッドを追加
    def get_replies(self, db_session):
        """このメッセージへの返信を取得するメソッド"""
        return db_session.query(Message).filter(Message.parent_message_id == self.message_id).all()