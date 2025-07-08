from datetime import datetime, timedelta, timezone
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from app.db import models
from app.db.models import Conversation, Message
from typing import Optional, List
import uuid

BRAZIL_TZ = pytz.timezone('America/Sao_Paulo')


def close_inactive_conversations(db: Session, inactivity_minutes: int = 60):
    cutoff_time = datetime.now(timezone.utc) - \
        timedelta(minutes=inactivity_minutes)

    open_conversations = db.query(models.Conversation).filter(
        models.Conversation.status == 'open'
    ).all()

    closed_count = 0

    for conversation in open_conversations:
        last_message = db.query(models.Message).filter(
            models.Message.conversation_id == conversation.id
        ).order_by(desc(models.Message.timestamp)).first()

        should_close = False

        if not last_message:
            should_close = conversation.start_time < cutoff_time
        else:
            should_close = last_message.timestamp < cutoff_time

        if should_close:
            conversation.status = 'closed'
            conversation.end_time = datetime.now(timezone.utc)
            closed_count += 1

    if closed_count > 0:
        db.commit()
        print(f"✅ Encerradas {closed_count} conversas inativas")

    return closed_count


def get_or_create_conversation(db: Session, user_number: str):

    # Limpar conversas inativas a cada chamada
    close_inactive_conversations(db)

    # Verificar se existe conversa aberta para este usuário
    last_conversation = db.query(models.Conversation).filter(
        models.Conversation.user_number == user_number,
        models.Conversation.status == 'open'
    ).order_by(desc(models.Conversation.start_time)).first()

    if last_conversation:
        sixty_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=60)

        last_message = db.query(models.Message).filter(
            models.Message.conversation_id == last_conversation.id
        ).order_by(desc(models.Message.timestamp)).first()

        if last_message and last_message.timestamp >= sixty_minutes_ago:
            return last_conversation
        else:
            # Esta conversa específica deve ser fechada
            last_conversation.status = 'closed'
            last_conversation.end_time = datetime.now(timezone.utc)
            db.commit()

    # Criar nova conversa
    new_conversation = models.Conversation(
        user_number=user_number,
        status='open',
        business_type='unknown'
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return new_conversation


def create_message(db: Session, user_number: str, content: str, from_user=True, business_type='unknown'):
    conversation = get_or_create_conversation(db, user_number)

    db_message = models.Message(
        user_number=user_number,
        content=content,
        from_user=from_user,
        business_type=business_type,
        conversation_id=conversation.id
    )

    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def convert_to_brazil_time(utc_datetime):
    """Converte UTC para horário do Brasil"""
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    return utc_datetime.astimezone(BRAZIL_TZ)


def get_conversation_stats(db: Session):
    """Retorna estatísticas das conversas"""

    # Conversas por status
    status_stats = db.query(
        models.Conversation.status,
        func.count(models.Conversation.id).label('count')
    ).group_by(models.Conversation.status).all()

    # Conversas abertas há mais de 1 hora
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    old_open = db.query(models.Conversation).filter(
        and_(
            models.Conversation.status == 'open',
            models.Conversation.start_time < one_hour_ago
        )
    ).count()

    return {
        'status_distribution': {row.status: row.count for row in status_stats},
        'old_open_conversations': old_open,
        'last_check': datetime.now(timezone.utc).isoformat()
    }


def get_conversation_by_id(db: Session, conversation_id: str) -> Optional[Conversation]:
    """
    Busca uma conversa pelo ID
    """
    try:
        # Converter string para UUID se necessário
        if isinstance(conversation_id, str):
            conversation_uuid = uuid.UUID(conversation_id)
        else:
            conversation_uuid = conversation_id

        return db.query(Conversation).filter(
            Conversation.id == conversation_uuid
        ).first()
    except ValueError:
        # ID inválido
        return None


def get_messages_by_conversation_id(db: Session, conversation_id: str) -> List[Message]:
    """
    Busca todas as mensagens de uma conversa específica
    """
    try:
        # Converter string para UUID se necessário
        if isinstance(conversation_id, str):
            conversation_uuid = uuid.UUID(conversation_id)
        else:
            conversation_uuid = conversation_id

        return db.query(Message).filter(
            Message.conversation_id == conversation_uuid
        ).order_by(Message.timestamp.asc()).all()
    except ValueError:
        # ID inválido
        return []
