from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db import crud
from app.core import message_handler
from fastapi.responses import JSONResponse

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post('/webhook')
async def receive_message(payload: dict, db: Session = Depends(get_db)):
    user_number = payload.get('user_number', 'unknown')
    content = payload.get('message', '')

    saved_message = crud.create_message(db, user_number, content)

    result = message_handler.process_message(
        db=db,
        user_number=user_number,
        content=content,
        conversation_id=saved_message.conversation_id
    )

    return JSONResponse(content={
        "reply": result.get("reply"),
        "sentiment": result.get("sentiment"),
        "score": result.get("score")
    })
