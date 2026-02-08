"""Chat router for the Todo AI Chatbot."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from sqlmodel import Session
from app.database import get_session
from app.services.chat_service import ChatService
from pydantic import BaseModel


router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    conversation_id: Optional[str] = None


class ToolCallResponse(BaseModel):
    """Response model for tool calls."""
    id: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    created_at: str


class MessageResponse(BaseModel):
    """Response model for messages."""
    id: str
    role: str
    content: str
    created_at: str
    tool_calls: List[ToolCallResponse] = []


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    conversation_id: str
    message: MessageResponse
    tool_calls: List[Dict[str, Any]]
    need_clarification: bool = False


@router.post("/api/{user_id}/chat", response_model=ChatResponse)
async def send_chat_message(
    user_id: str,
    request: ChatRequest,
    db_session: Session = Depends(get_session)
):
    """
    Send a message to the AI assistant and receive a response.

    Args:
        user_id: The ID of the user sending the message (string format from Better Auth)
        request: The chat request containing the message and optional conversation ID
        db_session: Database session

    Returns:
        ChatResponse with the assistant's reply and any tool calls
    """
    try:
        # Initialize chat service
        chat_service = ChatService(db_session)

        # Process conversation_id if provided
        conversation_id = None
        if request.conversation_id:
            try:
                conversation_id = UUID(request.conversation_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid conversation ID format")

        # Process the message
        result = await chat_service.process_chat_message(
            user_id,  # Pass string user_id directly
            request.message,
            conversation_id
        )

        # Convert the result to the expected response format
        response = ChatResponse(
            conversation_id=str(result["conversation_id"]),
            message=MessageResponse(
                id=result["message"]["id"],
                role=result["message"]["role"],
                content=result["message"]["content"],
                created_at=result["message"]["created_at"],
                tool_calls=[]
            ),
            tool_calls=result["tool_calls"],
            need_clarification=result.get("need_clarification", False)
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class ConversationResponse(BaseModel):
    """Response model for conversation."""
    id: str
    user_id: str
    created_at: str
    updated_at: str


@router.get("/api/{user_id}/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    user_id: str,
    db_session: Session = Depends(get_session)
):
    """
    Get all conversations for the authenticated user.

    Args:
        user_id: The ID of the user
        db_session: Database session

    Returns:
        List of conversations for the user
    """
    try:
        # In a real implementation, we would query the database for conversations
        # For now, return an empty list as a placeholder
        return []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class ConversationWithMessagesResponse(ConversationResponse):
    """Response model for conversation with messages."""
    messages: List[MessageResponse]


@router.get("/api/{user_id}/conversations/{conversation_id}", response_model=ConversationWithMessagesResponse)
async def get_conversation(
    user_id: str,
    conversation_id: str,
    db_session: Session = Depends(get_session)
):
    """
    Get a specific conversation with all messages and tool calls.

    Args:
        user_id: The ID of the user
        conversation_id: The ID of the conversation
        db_session: Database session

    Returns:
        Conversation with all its messages
    """
    try:
        # Validate conversation_id format
        try:
            conv_uuid = UUID(conversation_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")

        # Initialize chat service
        chat_service = ChatService(db_session)

        # Get conversation history
        messages = chat_service.get_conversation_history(user_id, conv_uuid)

        return ConversationWithMessagesResponse(
            id=conversation_id,
            user_id=user_id,
            created_at="2026-01-20T00:00:00Z",
            updated_at="2026-01-20T00:00:00Z",
            messages=[
                MessageResponse(
                    id=msg["id"],
                    role=msg["role"],
                    content=msg["content"],
                    created_at=msg["created_at"],
                    tool_calls=[]
                )
                for msg in messages
            ]
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/api/{user_id}/conversations/{conversation_id}")
async def delete_conversation(
    user_id: str,
    conversation_id: str,
    db_session: Session = Depends(get_session)
):
    """
    Delete a conversation and all its messages.

    Args:
        user_id: The ID of the user
        conversation_id: The ID of the conversation to delete
        db_session: Database session

    Returns:
        Empty response with 204 status code
    """
    try:
        # Validate conversation_id format
        try:
            conv_uuid = UUID(conversation_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")

        # In a real implementation, we would delete the conversation from the database
        return None

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
