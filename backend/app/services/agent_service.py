"""Agent service for the Todo AI Chatbot using OpenAI SDK with GPT-5 mini."""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from sqlmodel import Session
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from app.mcp.task_tools import create_task_tools

load_dotenv()


class OpenAIAgentService:
    """Service to handle AI agent interactions using OpenAI GPT-5 mini model."""

    def __init__(self):
        """Initialize the OpenAI agent service with lazy loading."""
        self._provider = None
        self._model = None

    @property
    def provider(self):
        """Lazy initialization of the OpenAI provider."""
        if self._provider is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")

            self._provider = AsyncOpenAI(
                api_key=openai_api_key,
            )
        return self._provider

    @property
    def model(self):
        """Lazy initialization of the model."""
        if self._model is None:
            self._model = OpenAIChatCompletionsModel(
                model="gpt-5-mini",
                openai_client=self.provider
            )
        return self._model

    def create_agent(self, db_session: Session, user_id: str) -> Agent:
        """
        Create an AI agent with task management tools.

        Args:
            db_session: Database session for task operations
            user_id: The ID of the current user

        Returns:
            Configured Agent instance
        """
        # Create task tools for this user
        tools = create_task_tools(db_session, user_id)

        # Create the agent with task management instructions
        agent = Agent(
            name="Todo Task Assistant",
            instructions="""You are a helpful AI Task Assistant for a Todo application. Your job is to help users manage their tasks.

You can perform the following actions:
1. **Add tasks**: When a user asks to add, create, or make a new task, use the add_task tool
2. **List tasks**: When a user asks to show, list, view, or see their tasks, use the list_tasks tool
3. **Complete tasks**: When a user asks to complete, finish, mark as done, or check off a task, use the complete_task tool
4. **Delete tasks**: When a user asks to delete, remove, or cancel a task, use the delete_task tool
5. **Update tasks**: When a user asks to update, change, rename, or modify a task, use the update_task tool

Guidelines:
- Always be friendly and helpful
- When adding tasks, extract the task title from the user's message
- When a task operation succeeds, confirm it with a friendly message
- When a task operation fails, explain why and suggest alternatives
- If the user's intent is unclear, ask for clarification
- Keep responses concise but informative

Example interactions:
- "Add task to buy groceries" -> Use add_task with title "buy groceries"
- "Show my tasks" -> Use list_tasks
- "Complete the groceries task" -> Use complete_task with task_title "groceries"
- "Delete the report task" -> Use delete_task with task_title "report"
""",
            model=self.model,
            tools=tools
        )

        return agent

    async def process_message(self, message: str, db_session: Session, user_id: str) -> Dict[str, Any]:
        """
        Process a user message and return the agent's response.

        Args:
            message: The user's message
            db_session: Database session for task operations
            user_id: The ID of the current user

        Returns:
            Dictionary with the response and tool calls
        """
        try:
            # Create agent with user-specific tools
            agent = self.create_agent(db_session, user_id)

            # Run the agent with the user's message
            result = await Runner.run(agent, message)

            # Extract tool calls from the result if any
            tool_calls = []
            if hasattr(result, 'raw_responses') and result.raw_responses:
                for response in result.raw_responses:
                    if hasattr(response, 'output') and response.output:
                        for item in response.output:
                            if hasattr(item, 'type') and item.type == 'function_call':
                                tool_calls.append({
                                    "name": item.name if hasattr(item, 'name') else "unknown",
                                    "arguments": item.arguments if hasattr(item, 'arguments') else {},
                                    "result": {}
                                })

            return {
                "response": result.final_output,
                "tool_calls": tool_calls,
                "need_clarification": False
            }

        except Exception as e:
            print(f"Agent error: {str(e)}")
            return {
                "response": f"I'm sorry, I encountered an error processing your request. Please try again.",
                "tool_calls": [],
                "need_clarification": False,
                "error": str(e)
            }


# Global agent service instance
openai_agent_service = OpenAIAgentService()
