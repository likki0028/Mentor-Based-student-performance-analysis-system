from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..dependencies import get_current_active_user

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(
    request: ChatRequest,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Answers project-related academic questions."""
    try:
        from ..services.chatbot_service import ChatbotService
        reply = ChatbotService.answer_question(db, current_user, request.message)
        return ChatResponse(reply=reply)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Assistant error: {str(e)}")
