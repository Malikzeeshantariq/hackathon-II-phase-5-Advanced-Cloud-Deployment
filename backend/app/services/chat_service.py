"""Chat service for the Todo AI Chatbot."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Session, select
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.tool_call import ToolCall
from app.services.agent_service import openai_agent_service


class ChatService:
    """Service to handle chat operations and conversation management."""

    def __init__(self, db_session: Session):
        """Initialize the chat service with a database session."""
        self.db_session = db_session

    def get_or_create_conversation(self, user_id: str) -> Conversation:
        """
        Get existing conversation for user or create a new one.

        Args:
            user_id: The ID of the user (string format)

        Returns:
            The conversation object
        """
        # Find existing conversation for the user
        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(1)
        )
        result = self.db_session.exec(statement)
        conversation = result.first()

        if conversation:
            return conversation

        # Create new conversation
        conversation = Conversation(
            id=uuid4(),
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db_session.add(conversation)
        self.db_session.commit()
        self.db_session.refresh(conversation)
        return conversation

    def add_user_message(self, conversation_id: UUID, content: str) -> Message:
        """
        Add a user message to the conversation.

        Args:
            conversation_id: The ID of the conversation
            content: The message content

        Returns:
            The created message object
        """
        message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            content=content,
            role=MessageRole.USER,
            created_at=datetime.utcnow()
        )
        self.db_session.add(message)
        self.db_session.commit()
        self.db_session.refresh(message)
        return message

    def add_assistant_message(self, conversation_id: UUID, content: str, tool_calls_data: List[Dict[str, Any]] = None) -> Message:
        """
        Add an assistant message to the conversation.

        Args:
            conversation_id: The ID of the conversation
            content: The message content
            tool_calls_data: List of tool calls made during this response

        Returns:
            The created message object
        """
        message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            content=content,
            role=MessageRole.ASSISTANT,
            created_at=datetime.utcnow()
        )
        self.db_session.add(message)
        self.db_session.commit()
        self.db_session.refresh(message)

        # If there are tool calls, save them as well
        if tool_calls_data:
            for tc_data in tool_calls_data:
                tool_call = ToolCall(
                    id=uuid4(),
                    message_id=message.id,
                    tool_name=tc_data.get("name", "unknown"),
                    parameters=tc_data.get("arguments", {}),
                    result=tc_data.get("result", {}),
                    created_at=datetime.utcnow()
                )
                self.db_session.add(tool_call)

            self.db_session.commit()

        return message

    async def process_chat_message(self, user_id: str, message_content: str, conversation_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Process a chat message from the user and return the assistant response.

        Args:
            user_id: The ID of the authenticated user (string format)
            message_content: The user's message
            conversation_id: Optional existing conversation ID

        Returns:
            Dictionary with response and conversation information
        """
        # Get or create conversation
        if conversation_id:
            # Verify that the conversation belongs to the user
            statement = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            result = self.db_session.exec(statement)
            conversation = result.first()

            if not conversation:
                raise ValueError("Conversation not found or does not belong to user")
        else:
            conversation = self.get_or_create_conversation(user_id)

        # Add user message to conversation
        user_message = self.add_user_message(conversation.id, message_content)

        # Process the message with the OpenAI agent service
        agent_response = await openai_agent_service.process_message(
            message_content,
            self.db_session,
            user_id
        )

        # Get the response content and tool calls
        response_content = agent_response.get("response", "I processed your request.")
        tool_calls = agent_response.get("tool_calls", [])

        # Add assistant message to conversation
        assistant_message = self.add_assistant_message(
            conversation.id,
            response_content,
            tool_calls
        )

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        self.db_session.commit()

        return {
            "conversation_id": conversation.id,
            "message": {
                "id": str(assistant_message.id),
                "role": "assistant",
                "content": response_content,
                "created_at": assistant_message.created_at.isoformat()
            },
            "tool_calls": tool_calls,
            "need_clarification": agent_response.get("need_clarification", False)
        }

    def get_conversation_history(self, user_id: str, conversation_id: UUID) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a specific conversation.

        Args:
            user_id: The ID of the user (string format)
            conversation_id: The ID of the conversation

        Returns:
            List of messages in the conversation
        """
        # Verify that the conversation belongs to the user
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        result = self.db_session.exec(statement)
        conversation = result.first()

        if not conversation:
            raise ValueError("Conversation not found or does not belong to user")

        # Get messages for the conversation
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = self.db_session.exec(statement)
        messages = result.all()

        message_list = []
        for msg in messages:
            # Get tool calls for this message
            tool_call_statement = select(ToolCall).where(ToolCall.message_id == msg.id)
            tool_call_result = self.db_session.exec(tool_call_statement)
            tool_calls = tool_call_result.all()

            message_dict = {
                "id": str(msg.id),
                "role": msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "tool_calls": [
                    {
                        "id": str(tc.id),
                        "tool_name": tc.tool_name,
                        "parameters": tc.parameters,
                        "result": tc.result,
                        "created_at": tc.created_at.isoformat()
                    }
                    for tc in tool_calls
                ]
            }
            message_list.append(message_dict)

        return message_list
