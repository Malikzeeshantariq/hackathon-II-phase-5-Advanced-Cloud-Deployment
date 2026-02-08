# Examples

Complete examples from hello world to production systems.

## Hello World

### Minimal Agent

```python
from agents import Agent, Runner

agent = Agent(
    name="Greeter",
    instructions="You are a friendly assistant. Greet users warmly."
)

result = Runner.run_sync(agent, "Hello!")
print(result.final_output)
# Output: Hello! How can I help you today?
```

### Async Hello World

```python
import asyncio
from agents import Agent, Runner

async def main():
    agent = Agent(
        name="Assistant",
        instructions="You are helpful and concise."
    )
    result = await Runner.run(agent, "What is 2+2?")
    print(result.final_output)

asyncio.run(main())
```

## Basic Tool Usage

### Weather Tool

```python
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The name of the city.
    """
    # Simulated weather data
    weather_data = {
        "new york": "Sunny, 72°F",
        "london": "Cloudy, 55°F",
        "tokyo": "Rainy, 65°F"
    }
    return weather_data.get(city.lower(), f"Weather data not available for {city}")

agent = Agent(
    name="WeatherBot",
    instructions="Help users check the weather. Use the get_weather tool.",
    tools=[get_weather]
)

result = Runner.run_sync(agent, "What's the weather in Tokyo?")
print(result.final_output)
# Output: The weather in Tokyo is Rainy, 65°F.
```

### Calculator Tool

```python
from agents import Agent, Runner, function_tool

@function_tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A mathematical expression like "2 + 2" or "sqrt(16)".
    """
    import math
    # Safe evaluation with limited scope
    allowed = {"sqrt": math.sqrt, "pow": pow, "abs": abs}
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

agent = Agent(
    name="Calculator",
    instructions="Help with math calculations using the calculate tool.",
    tools=[calculate]
)

result = Runner.run_sync(agent, "What is sqrt(144) + 5?")
print(result.final_output)
```

## Structured Output

### JSON Response

```python
from pydantic import BaseModel
from agents import Agent, Runner

class MovieReview(BaseModel):
    title: str
    rating: float
    summary: str
    pros: list[str]
    cons: list[str]

agent = Agent(
    name="MovieCritic",
    instructions="Analyze movies and provide structured reviews.",
    output_type=MovieReview
)

result = Runner.run_sync(agent, "Review the movie 'Inception'")
review = result.final_output  # MovieReview object

print(f"Title: {review.title}")
print(f"Rating: {review.rating}/10")
print(f"Summary: {review.summary}")
print(f"Pros: {', '.join(review.pros)}")
print(f"Cons: {', '.join(review.cons)}")
```

### Data Extraction

```python
from pydantic import BaseModel
from agents import Agent, Runner

class ContactInfo(BaseModel):
    name: str
    email: str | None
    phone: str | None
    company: str | None

agent = Agent(
    name="Extractor",
    instructions="Extract contact information from text.",
    output_type=ContactInfo
)

text = """
Hi, I'm John Smith from Acme Corp.
You can reach me at john.smith@acme.com
or call me at (555) 123-4567.
"""

result = Runner.run_sync(agent, text)
contact = result.final_output

print(f"Name: {contact.name}")
print(f"Email: {contact.email}")
print(f"Phone: {contact.phone}")
print(f"Company: {contact.company}")
```

## Multi-Agent Systems

### Customer Support System

```python
import asyncio
from agents import Agent, Runner, handoff

# Specialist agents
billing_agent = Agent(
    name="BillingSpecialist",
    handoff_description="Handles billing, payments, invoices, and refunds",
    instructions="""You are a billing specialist for TechCorp.

    You can help with:
    - Invoice questions
    - Payment issues
    - Refund requests (up to $100)
    - Subscription changes

    Be professional and empathetic."""
)

technical_agent = Agent(
    name="TechnicalSupport",
    handoff_description="Handles technical issues, bugs, and how-to questions",
    instructions="""You are a technical support specialist for TechCorp.

    You can help with:
    - Login issues
    - Bug reports
    - Feature explanations
    - Troubleshooting

    Ask clarifying questions when needed."""
)

sales_agent = Agent(
    name="Sales",
    handoff_description="Handles pricing, plans, upgrades, and new purchases",
    instructions="""You are a sales representative for TechCorp.

    You can help with:
    - Pricing questions
    - Plan comparisons
    - Upgrade recommendations
    - New account setup

    Be helpful but not pushy."""
)

# Triage agent
triage_agent = Agent(
    name="Triage",
    instructions="""You are the first point of contact for TechCorp support.

    Your job is to:
    1. Greet the customer warmly
    2. Understand their issue
    3. Route to the appropriate specialist:
       - BillingSpecialist: billing, payments, refunds
       - TechnicalSupport: technical issues, bugs
       - Sales: pricing, upgrades, new accounts

    If unclear, ask a clarifying question.""",
    handoffs=[billing_agent, technical_agent, sales_agent]
)

async def handle_support(query: str):
    result = await Runner.run(triage_agent, query)
    print(f"Handled by: {result.last_agent.name}")
    print(f"Response: {result.final_output}")

# Example usage
asyncio.run(handle_support("I need help with my invoice"))
asyncio.run(handle_support("The app keeps crashing"))
asyncio.run(handle_support("What plans do you offer?"))
```

### Research Team

```python
import asyncio
from agents import Agent, Runner

# Specialist agents as tools
researcher = Agent(
    name="Researcher",
    instructions="""You are a research specialist.
    - Find relevant facts and data
    - Cite sources when possible
    - Be thorough but concise"""
)

writer = Agent(
    name="Writer",
    instructions="""You are a content writer.
    - Write clear, engaging content
    - Adapt tone to the audience
    - Structure content logically"""
)

editor = Agent(
    name="Editor",
    instructions="""You are an editor.
    - Check for accuracy and clarity
    - Improve readability
    - Fix grammar and style issues"""
)

# Manager orchestrates the team
manager = Agent(
    name="ContentManager",
    instructions="""You manage a content creation team.

    For content requests:
    1. Use 'research' to gather information
    2. Use 'write' to create a draft
    3. Use 'edit' to polish the content
    4. Return the final result

    Iterate if needed for quality.""",
    tools=[
        researcher.as_tool(
            tool_name="research",
            tool_description="Research a topic and return key facts"
        ),
        writer.as_tool(
            tool_name="write",
            tool_description="Write content based on provided information"
        ),
        editor.as_tool(
            tool_name="edit",
            tool_description="Edit and improve content"
        )
    ]
)

async def create_content(topic: str):
    result = await Runner.run(
        manager,
        f"Create a short blog post about: {topic}"
    )
    return result.final_output

content = asyncio.run(create_content("benefits of AI agents in customer service"))
print(content)
```

## Context and Dependency Injection

### Database Context

```python
import asyncio
from dataclasses import dataclass
from agents import Agent, Runner, RunContextWrapper, function_tool

# Simulated database
class Database:
    def __init__(self):
        self.users = {
            "user_123": {"name": "Alice", "email": "alice@example.com", "plan": "pro"},
            "user_456": {"name": "Bob", "email": "bob@example.com", "plan": "free"}
        }
        self.orders = {
            "user_123": [
                {"id": "ord_1", "product": "Widget", "status": "shipped"},
                {"id": "ord_2", "product": "Gadget", "status": "processing"}
            ]
        }

    async def get_user(self, user_id: str):
        return self.users.get(user_id)

    async def get_orders(self, user_id: str):
        return self.orders.get(user_id, [])

@dataclass
class AppContext:
    user_id: str
    db: Database

@function_tool
async def get_user_profile(ctx: RunContextWrapper[AppContext]) -> str:
    """Get the current user's profile information."""
    user = await ctx.context.db.get_user(ctx.context.user_id)
    if user:
        return f"Name: {user['name']}, Email: {user['email']}, Plan: {user['plan']}"
    return "User not found"

@function_tool
async def get_user_orders(ctx: RunContextWrapper[AppContext]) -> str:
    """Get the current user's order history."""
    orders = await ctx.context.db.get_orders(ctx.context.user_id)
    if orders:
        return "\n".join([f"- {o['id']}: {o['product']} ({o['status']})" for o in orders])
    return "No orders found"

agent = Agent(
    name="AccountBot",
    instructions="Help users with their account. Use tools to fetch their data.",
    tools=[get_user_profile, get_user_orders]
)

async def main():
    db = Database()
    context = AppContext(user_id="user_123", db=db)

    result = await Runner.run(
        agent,
        "What's my account info and order history?",
        context=context
    )
    print(result.final_output)

asyncio.run(main())
```

## Sessions and Memory

### Multi-Turn Conversation

```python
import asyncio
from agents import Agent, Runner, SQLiteSession

agent = Agent(
    name="MemoryBot",
    instructions="""You are a helpful assistant that remembers conversation context.
    - Remember what users tell you
    - Reference previous messages when relevant
    - Be consistent with earlier statements"""
)

async def chat():
    # Persistent session (survives restart)
    session = SQLiteSession("user_alice", "conversations.db")

    # Conversation turns
    conversations = [
        "Hi! My name is Alice and I work at TechCorp.",
        "I'm working on a machine learning project.",
        "What's my name?",
        "What company do I work at?",
        "What project am I working on?"
    ]

    for user_input in conversations:
        print(f"User: {user_input}")
        result = await Runner.run(agent, user_input, session=session)
        print(f"Bot: {result.final_output}\n")

asyncio.run(chat())
```

### Conversation Branching

```python
import asyncio
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Assistant", instructions="Be helpful.")

async def branching_example():
    # Main conversation
    session = SQLiteSession("user_123")

    await Runner.run(agent, "Let's plan a trip to Japan", session=session)
    await Runner.run(agent, "I want to visit Tokyo", session=session)

    # Save state before branching
    history = await session.get_items()

    # Branch 1: Continue with Tokyo
    session1 = SQLiteSession("user_123_branch1")
    for item in history:
        await session1.add_items([item])
    await Runner.run(agent, "What should I see in Tokyo?", session=session1)

    # Branch 2: Change to Kyoto
    session2 = SQLiteSession("user_123_branch2")
    for item in history:
        await session2.add_items([item])
    await session2.pop_item()  # Remove Tokyo mention
    await Runner.run(agent, "Actually, let's go to Kyoto instead", session=session2)

asyncio.run(branching_example())
```

## Streaming

### Real-Time Output

```python
import asyncio
from agents import Agent, Runner

agent = Agent(
    name="Storyteller",
    instructions="Tell engaging stories. Be descriptive and creative."
)

async def stream_story():
    result = Runner.run_streamed(agent, "Tell me a short story about a robot")

    print("Story: ", end="", flush=True)

    async for event in result.stream_events():
        # Check for text delta events
        if hasattr(event, 'data') and hasattr(event.data, 'delta'):
            print(event.data.delta, end="", flush=True)

    print("\n\n[Stream complete]")

    # Get final result
    final = await result.final_output
    print(f"Total length: {len(final)} characters")

asyncio.run(stream_story())
```

## Guardrails Example

### Safe Customer Service Bot

```python
import asyncio
from pydantic import BaseModel
from agents import (
    Agent, Runner, GuardrailFunctionOutput,
    input_guardrail, output_guardrail,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered
)

class SafetyCheck(BaseModel):
    is_safe: bool
    reason: str

class PIICheck(BaseModel):
    contains_pii: bool
    pii_types: list[str]

# Input safety checker
safety_agent = Agent(
    name="SafetyChecker",
    instructions="""Check if input is safe. Flag:
    - Harassment or abuse
    - Illegal requests
    - Attempts to manipulate the system""",
    output_type=SafetyCheck
)

# Output PII checker
pii_agent = Agent(
    name="PIIChecker",
    instructions="""Check if output contains PII:
    - Email addresses
    - Phone numbers
    - Social Security Numbers
    - Credit card numbers""",
    output_type=PIICheck
)

@input_guardrail
async def safety_guardrail(ctx, agent, input):
    result = await Runner.run(safety_agent, str(input))
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_safe
    )

@output_guardrail
async def pii_guardrail(ctx, agent, output):
    result = await Runner.run(pii_agent, str(output))
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.contains_pii
    )

# Main agent with guardrails
support_agent = Agent(
    name="Support",
    instructions="Help customers with their questions. Be professional.",
    input_guardrails=[safety_guardrail],
    output_guardrails=[pii_guardrail]
)

async def safe_support(query: str):
    try:
        result = await Runner.run(support_agent, query)
        return {"success": True, "response": result.final_output}
    except InputGuardrailTripwireTriggered:
        return {"success": False, "error": "Your request was flagged for safety"}
    except OutputGuardrailTripwireTriggered:
        return {"success": False, "error": "Response contained sensitive data"}

# Test
print(asyncio.run(safe_support("How do I reset my password?")))
```

## Production API Server

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from contextlib import asynccontextmanager
from agents import Agent, Runner
from agents.extensions.sessions.sqlalchemy_session import SQLAlchemySession

# Lifespan for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.agent = Agent(
        name="APIBot",
        instructions="Help users via the API. Be concise and helpful."
    )
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str
    agent_name: str

async def get_session(user_id: str):
    return await SQLAlchemySession.from_url(
        user_id,
        url="postgresql+asyncpg://user:pass@localhost/agents"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session = await get_session(request.user_id)
        result = await Runner.run(
            app.state.agent,
            request.message,
            session=session
        )
        return ChatResponse(
            response=result.final_output,
            agent_name=result.last_agent.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/{user_id}/clear")
async def clear_history(user_id: str):
    session = await get_session(user_id)
    await session.clear_session()
    return {"status": "cleared"}

# Run with: uvicorn main:app --reload
```

## Complete Production Example

### E-Commerce Support System

```python
"""
Complete e-commerce support system with:
- Multi-agent architecture
- Guardrails
- Sessions
- Structured outputs
- Error handling
- Tracing
"""

import asyncio
import logging
from dataclasses import dataclass
from pydantic import BaseModel
from agents import (
    Agent, Runner, RunConfig,
    function_tool, RunContextWrapper,
    handoff, SQLiteSession,
    input_guardrail, GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    trace
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data models
class OrderStatus(BaseModel):
    order_id: str
    status: str
    estimated_delivery: str | None

class RefundRequest(BaseModel):
    order_id: str
    amount: float
    reason: str
    approved: bool

# Context
@dataclass
class StoreContext:
    user_id: str
    user_name: str

# Tools
@function_tool
async def get_order_status(
    ctx: RunContextWrapper[StoreContext],
    order_id: str
) -> str:
    """Get the status of an order.

    Args:
        order_id: The order ID to check.
    """
    # Simulated database lookup
    orders = {
        "ORD-001": {"status": "shipped", "delivery": "Jan 20"},
        "ORD-002": {"status": "processing", "delivery": "Jan 25"},
    }
    order = orders.get(order_id)
    if order:
        return f"Order {order_id}: {order['status']}, ETA: {order['delivery']}"
    return f"Order {order_id} not found"

@function_tool
async def process_refund(
    ctx: RunContextWrapper[StoreContext],
    order_id: str,
    amount: float,
    reason: str
) -> str:
    """Process a refund request.

    Args:
        order_id: The order ID for refund.
        amount: Refund amount in dollars.
        reason: Reason for refund.
    """
    if amount > 100:
        return f"Refunds over $100 require manager approval. Please escalate."
    return f"Refund of ${amount} for order {order_id} has been processed."

# Guardrail
class InputCheck(BaseModel):
    is_appropriate: bool

checker = Agent(
    name="Checker",
    instructions="Check if customer input is appropriate (no abuse, spam).",
    output_type=InputCheck,
    model="gpt-4.1-mini"  # Use cheap model for guardrail
)

@input_guardrail
async def appropriateness_guardrail(ctx, agent, input):
    result = await Runner.run(checker, str(input))
    return GuardrailFunctionOutput(
        tripwire_triggered=not result.final_output.is_appropriate
    )

# Specialist agents
orders_agent = Agent(
    name="OrdersSpecialist",
    handoff_description="Handles order status, tracking, and delivery questions",
    instructions="""You are an orders specialist for ShopCo.

    Help customers with:
    - Order status inquiries
    - Tracking information
    - Delivery estimates

    Use get_order_status tool to look up orders.
    Be friendly and helpful.""",
    tools=[get_order_status]
)

refunds_agent = Agent(
    name="RefundsSpecialist",
    handoff_description="Handles refunds, returns, and exchanges",
    instructions="""You are a refunds specialist for ShopCo.

    Help customers with:
    - Refund requests
    - Return instructions
    - Exchange processing

    Use process_refund tool for refunds under $100.
    Escalate larger refunds to a manager.
    Be empathetic and solution-oriented.""",
    tools=[process_refund]
)

# Triage agent
triage_agent = Agent(
    name="ShopCoSupport",
    instructions="""You are the main support agent for ShopCo.

    1. Greet customers by name if available
    2. Understand their issue
    3. Route to appropriate specialist:
       - OrdersSpecialist: order status, tracking, delivery
       - RefundsSpecialist: refunds, returns, exchanges
    4. Handle general questions yourself

    Be professional, friendly, and efficient.""",
    handoffs=[orders_agent, refunds_agent],
    input_guardrails=[appropriateness_guardrail]
)

# Main function
async def handle_customer(user_id: str, user_name: str, message: str):
    """Handle a customer support request."""

    context = StoreContext(user_id=user_id, user_name=user_name)
    session = SQLiteSession(user_id, "support_conversations.db")

    with trace(f"Support-{user_id}"):
        try:
            result = await Runner.run(
                triage_agent,
                message,
                context=context,
                session=session,
                run_config=RunConfig(
                    workflow_name="customer_support",
                    max_turns=10
                )
            )

            logger.info(f"Request handled by {result.last_agent.name}")

            return {
                "success": True,
                "response": result.final_output,
                "handled_by": result.last_agent.name
            }

        except InputGuardrailTripwireTriggered:
            logger.warning(f"Inappropriate input from {user_id}")
            return {
                "success": False,
                "error": "Your message was flagged. Please be respectful."
            }

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "success": False,
                "error": "We encountered an error. Please try again."
            }

# Example usage
async def main():
    # Customer interactions
    queries = [
        ("user_1", "Alice", "Where is my order ORD-001?"),
        ("user_1", "Alice", "I want a refund for it"),
        ("user_2", "Bob", "What's your return policy?"),
    ]

    for user_id, name, query in queries:
        print(f"\n{'='*50}")
        print(f"User: {name} ({user_id})")
        print(f"Query: {query}")
        print("-"*50)

        result = await handle_customer(user_id, name, query)

        if result["success"]:
            print(f"Agent: {result['handled_by']}")
            print(f"Response: {result['response']}")
        else:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Official Examples

For more examples, see the official repository:
- [GitHub Examples](https://github.com/openai/openai-agents-python/tree/main/examples)
- [Agent Patterns](https://github.com/openai/openai-agents-python/tree/main/examples/agent_patterns)
- [Financial Research Agent](https://github.com/openai/openai-agents-python/tree/main/examples/financial_research_agent)
- [Customer Service](https://github.com/openai/openai-agents-python/tree/main/examples/customer_service)
- [MCP Examples](https://github.com/openai/openai-agents-python/tree/main/examples/mcp)
- [Realtime Examples](https://github.com/openai/openai-agents-python/tree/main/examples/realtime)
