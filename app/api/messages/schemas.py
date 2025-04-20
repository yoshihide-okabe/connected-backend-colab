# app/api/messages/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from ...schemas.base import BaseSchemaModel

class MessageBase(BaseSchemaModel):
    content: str = Field(..., min_length=1, description="メッセージの内容")

class MessageCreate(MessageBase):
    trouble_id: int = Field(..., description="関連するお困りごとID")

class MessageResponse(MessageBase):
    message_id: int  # idからmessage_idに変更
    sender_user_id: int  # user_idからsender_user_idに変更
    sender_name: str  # user_nameからsender_nameに変更（計算値）
    trouble_id: int
    sent_at: datetime  # created_atからsent_atに変更
    parent_message_id: Optional[int] = None  # 親メッセージID追加

class MessagesListResponse(BaseSchemaModel):
    messages: List[MessageResponse]
    total: int