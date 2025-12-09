"""
Chat API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.claude_service import chat_with_opus

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    error: str = None

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Send a message to Claude Opus and get a response
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    response_text, error = chat_with_opus(request.message, request.model)
    
    if error:
        raise HTTPException(status_code=500, detail=error)
    
    return ChatResponse(response=response_text)

