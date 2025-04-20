# app/api/messages/models.py
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 相対インポートに変更
from ...core.database import Base

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, index=True)
    trouble_id = Column(Integer, ForeignKey("troubles.trouble_id"), nullable=False)
    sender_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    parent_message_id = Column(Integer, ForeignKey("messages.message_id"), nullable=True) 
    
    # リレーションシップ
    sender = relationship("User", back_populates="messages")
    trouble = relationship("Trouble", back_populates="messages")
    replies = relationship("Message", backref="parent", remote_side=[message_id]) 