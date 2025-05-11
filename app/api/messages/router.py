# app/api/messages/router.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ..auth.jwt import get_current_user
# from ...core.dependencies import get_current_user
from ..users.models import User
from ..troubles.models import Trouble
from .models import Message
from . import schemas

router = APIRouter()

@router.post("/", response_model=schemas.MessageResponse)
def create_message(
    message: schemas.MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    新しいメッセージを作成する
    """
    # お困りごとの存在確認
    trouble = db.query(Trouble).filter(Trouble.trouble_id == message.trouble_id).first()
    if not trouble:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたお困りごとが見つかりません"
        )
    
    # 親メッセージの存在確認（指定されている場合）
    if message.parent_message_id:
        parent_message = db.query(Message).filter(Message.message_id == message.parent_message_id).first()
        if not parent_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された親メッセージが見つかりません"
            )
    
    # 新しいメッセージを作成
    new_message = Message(
        content=message.content,
        sender_user_id=current_user.user_id,  # user_idからsender_user_idに変更
        trouble_id=message.trouble_id,
        parent_message_id=message.parent_message_id
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    return schemas.MessageResponse(
        message_id=new_message.message_id,  # idからmessage_idに変更
        content=new_message.content,
        sender_user_id=new_message.sender_user_id,  # user_idからsender_user_idに変更
        sender_name=current_user.name,  # user_nameからsender_nameに変更
        trouble_id=new_message.trouble_id,
        sent_at=new_message.sent_at,  # created_atからsent_atに変更
        parent_message_id=new_message.parent_message_id
    )

@router.get("/trouble/{trouble_id}", response_model=schemas.MessagesListResponse)
def get_messages_by_trouble(
    trouble_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    特定のお困りごとに関するメッセージの一覧を取得する
    """
    # お困りごとの存在確認
    trouble = db.query(Trouble).filter(Trouble.trouble_id == trouble_id).first()
    if not trouble:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたお困りごとが見つかりません"
        )
    
    # メッセージの取得
    query = db.query(Message).filter(Message.trouble_id == trouble_id)
    total = query.count()

    messages = query.order_by(Message.sent_at).offset(skip).limit(limit).all()
    
    # レスポンスの作成
    message_responses = []
    for msg in messages:
        user = db.query(User).filter(User.user_id == msg.sender_user_id).first()
        message_responses.append(schemas.MessageResponse(
            message_id=msg.message_id,
            content=msg.content,
            sender_user_id=msg.sender_user_id,
            sender_name=user.name if user else "Unknown",
            trouble_id=msg.trouble_id,
            sent_at=msg.sent_at,
            parent_message_id=msg.parent_message_id
        ))
    
    return schemas.MessagesListResponse(
        messages=message_responses,
        total=total
    )