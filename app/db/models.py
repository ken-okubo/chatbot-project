from sqlalchemy import Column, String, DateTime, func, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_number = Column(String, index=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    business_type = Column(String, default='unknown')
    status = Column(String, default='open')
    needs_human = Column(Boolean, default=False)
    # 'POSITIVO', 'NEUTRO', 'NEGATIVO'
    sentiment = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)  # -1.0 a 1.0
    last_sentiment_update = Column(DateTime(timezone=True), nullable=True)
    messages = relationship('Message', back_populates='conversation')


class Message(Base):
    __tablename__ = 'messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey(
        'conversations.id'), index=True)
    user_number = Column(String, index=True)
    content = Column(String)
    from_user = Column(Boolean, default=True)
    business_type = Column(String, default='unknown')
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship('Conversation', back_populates='messages')
