# ChatKit Server Patterns

Production patterns for ChatKit Server implementations.

---

## Server Patterns

### Basic Server Factory
```python
# app/server.py
from chatkit.server import ChatKitServer
from chatkit.store import MemoryStore
from chatkit.types import ThreadMetadata, UserMessageItem, ThreadStreamEvent
from chatkit.agents import AgentContext, stream_agent_response
from agents import Runner
from typing import AsyncIterator
from app.agents.assistant import assistant

class AssistantServer(ChatKitServer[dict]):
    def __init__(self, store=None):
        super().__init__(store=store or MemoryStore())
        self.assistant = assistant

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        agent_input = await self._to_agent_input(thread, item)
        if agent_input is None:
            return

        result = Runner.run_streamed(
            self.assistant,
            agent_input,
            context=agent_context,
        )

        async for event in stream_agent_response(agent_context, result):
            yield event

# Singleton for simple cases
server = AssistantServer()

# Factory for per-user servers
async def create_server(user_id: str) -> AssistantServer:
    store = await get_user_store(user_id)
    return AssistantServer(store=store)
```

### Multi-Tenant Server
```python
# app/server.py
from chatkit.server import ChatKitServer
from typing import AsyncIterator

class MultiTenantServer(ChatKitServer[dict]):
    def __init__(self, store, tenant_id: str):
        super().__init__(store=store)
        self.tenant_id = tenant_id
        self.assistant = self._create_tenant_agent(tenant_id)

    def _create_tenant_agent(self, tenant_id: str):
        config = get_tenant_config(tenant_id)
        return Agent[AgentContext](
            model=config.model,
            name=config.assistant_name,
            instructions=config.instructions,
            tools=self._get_tenant_tools(config),
        )

    async def respond(self, thread, item, context) -> AsyncIterator:
        # Inject tenant context
        context["tenant_id"] = self.tenant_id
        # ... rest of implementation
```

---

## Agent Patterns

### Agent with System Context
```python
# app/agents/assistant.py
from agents import Agent
from chatkit.agents import AgentContext
from datetime import datetime

def create_assistant(user_name: str = None) -> Agent[AgentContext]:
    base_instructions = """
You are a helpful AI assistant for Acme Corp.
Current date: {date}
{user_context}

Guidelines:
- Be concise and helpful
- Use tools when appropriate
- Never make up information
"""

    user_context = f"User: {user_name}" if user_name else ""
    instructions = base_instructions.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        user_context=user_context
    )

    return Agent[AgentContext](
        model="gpt-4.1-mini",
        name="Acme Assistant",
        instructions=instructions,
        tools=[search_docs, get_user_info, create_ticket],
    )
```

### Multi-Agent Router
```python
# app/agents/router.py
from agents import Agent
from chatkit.agents import AgentContext

# Specialized agents
support_agent = Agent[AgentContext](
    model="gpt-4.1-mini",
    name="Support Agent",
    instructions="You handle customer support queries...",
    tools=[search_tickets, create_ticket, escalate],
)

sales_agent = Agent[AgentContext](
    model="gpt-4.1-mini",
    name="Sales Agent",
    instructions="You help with pricing and demos...",
    tools=[get_pricing, schedule_demo, send_proposal],
)

general_agent = Agent[AgentContext](
    model="gpt-4.1-mini",
    name="General Assistant",
    instructions="You help with general questions...",
    tools=[search_docs, get_faq],
)

AGENTS = {
    "support": support_agent,
    "sales": sales_agent,
    "general": general_agent,
}

async def route_message(message: str) -> str:
    """Route message to appropriate agent."""
    message_lower = message.lower()

    # Keyword-based routing
    if any(kw in message_lower for kw in ["order", "refund", "issue", "problem", "help"]):
        return "support"
    if any(kw in message_lower for kw in ["price", "cost", "demo", "buy", "plan"]):
        return "sales"
    return "general"

# In server.respond():
async def respond(self, thread, item, context):
    agent_key = await route_message(item.content if item else "")
    agent = AGENTS[agent_key]
    # ... run agent
```

### Agent with Memory
```python
# app/agents/memory_agent.py
from agents import Agent, function_tool, RunContextWrapper
from chatkit.agents import AgentContext

# In-memory facts (replace with database in production)
user_facts: dict[str, list[str]] = {}

@function_tool(description_override="Save a fact about the user for future reference")
async def remember_fact(
    ctx: RunContextWrapper[AgentContext],
    fact: str
) -> dict:
    user_id = ctx.context.request_context.get("user_id", "default")
    if user_id not in user_facts:
        user_facts[user_id] = []
    user_facts[user_id].append(fact)
    return {"status": "remembered", "fact": fact}

@function_tool(description_override="Recall facts about the user")
async def recall_facts(
    ctx: RunContextWrapper[AgentContext]
) -> dict:
    user_id = ctx.context.request_context.get("user_id", "default")
    facts = user_facts.get(user_id, [])
    return {"facts": facts, "count": len(facts)}

memory_agent = Agent[AgentContext](
    model="gpt-4.1-mini",
    name="Memory Assistant",
    instructions="""
You are an assistant that remembers things about users.
When users share personal information, use remember_fact to save it.
When users ask "what do you know about me", use recall_facts.
""",
    tools=[remember_fact, recall_facts],
)
```

---

## Tool Patterns

### Database Tool
```python
@function_tool(description_override="Search products in the catalog")
async def search_products(
    ctx: RunContextWrapper[AgentContext],
    query: str,
    category: str | None = None,
    max_results: int = 5
) -> dict | None:
    try:
        async with get_db_session() as session:
            stmt = select(Product).where(
                Product.name.ilike(f"%{query}%")
            )
            if category:
                stmt = stmt.where(Product.category == category)
            stmt = stmt.limit(max_results)

            result = await session.execute(stmt)
            products = result.scalars().all()

            return {
                "products": [
                    {"id": p.id, "name": p.name, "price": p.price}
                    for p in products
                ],
                "count": len(products)
            }
    except Exception as e:
        logger.error(f"Product search failed: {e}")
        return None
```

### External API Tool
```python
import httpx

@function_tool(description_override="Get current weather for a city")
async def get_weather(
    ctx: RunContextWrapper[AgentContext],
    city: str,
    units: str = "metric"
) -> dict | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "units": units,
                    "appid": settings.weather_api_key
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            return {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "condition": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"]
            }
    except httpx.TimeoutException:
        logger.warning(f"Weather API timeout for {city}")
        return None
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return None
```

### Tool with Widget Output
```python
from chatkit.widgets import Card, Text, Image

@function_tool(description_override="Display product details with rich UI")
async def show_product(
    ctx: RunContextWrapper[AgentContext],
    product_id: str
) -> dict | None:
    product = await get_product(product_id)
    if not product:
        return None

    # Build widget
    widget = Card(children=[
        Image(src=product.image_url, alt=product.name, width=200, height=200),
        Text(value=product.name, size="xl", weight="bold"),
        Text(value=f"${product.price:.2f}", size="lg", color="primary"),
        Text(value=product.description, size="md", color="secondary"),
    ])

    # Stream to frontend
    await ctx.context.stream_widget(
        widget,
        copy_text=f"{product.name} - ${product.price:.2f}"
    )

    return {
        "product_id": product.id,
        "name": product.name,
        "price": product.price
    }
```

### Tool with Client Tool Trigger
```python
from chatkit.agents import ClientToolCall

@function_tool(description_override="Add item to shopping cart")
async def add_to_cart(
    ctx: RunContextWrapper[AgentContext],
    product_id: str,
    quantity: int = 1
) -> dict:
    # Validate
    product = await get_product(product_id)
    if not product:
        return {"error": "Product not found"}

    # Trigger frontend cart update
    ctx.context.client_tool_call = ClientToolCall(
        name="update_cart",
        arguments={
            "action": "add",
            "product_id": product_id,
            "product_name": product.name,
            "quantity": quantity,
            "price": product.price
        }
    )

    return {
        "status": "added",
        "product": product.name,
        "quantity": quantity
    }
```

---

## Frontend Integration Patterns

### React ChatKit Setup
```typescript
// components/ChatPanel.tsx
import { useChatKit, ChatKit } from "@openai/chatkit-react";

interface ChatPanelProps {
  theme: "light" | "dark";
  onThemeChange: (theme: "light" | "dark") => void;
  authToken: string;
}

export function ChatPanel({ theme, onThemeChange, authToken }: ChatPanelProps) {
  const chatkit = useChatKit({
    api: {
      url: process.env.NEXT_PUBLIC_API_URL + "/chatkit",
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    },
    theme: {
      colorScheme: theme,
      radius: "round",
    },
    startScreen: {
      greeting: "Hi! How can I help you today?",
      prompts: [
        "What can you help me with?",
        "Search for products",
        "Check my order status",
      ],
    },
    onClientTool: async (invocation) => {
      switch (invocation.name) {
        case "switch_theme":
          const newTheme = invocation.params.theme as "light" | "dark";
          onThemeChange(newTheme);
          return { success: true };

        case "update_cart":
          await cartStore.addItem({
            productId: invocation.params.product_id,
            quantity: invocation.params.quantity,
          });
          return { success: true };

        case "navigate":
          router.push(invocation.params.path);
          return { success: true };

        default:
          console.warn(`Unknown client tool: ${invocation.name}`);
          return { success: false };
      }
    },
    onError: ({ error }) => {
      console.error("ChatKit error:", error);
      toast.error("Something went wrong. Please try again.");
    },
  });

  return <ChatKit control={chatkit.control} className="h-full w-full" />;
}
```

### Next.js API Route (Alternative to Direct Backend)
```typescript
// app/api/chatkit/route.ts
import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  const authHeader = request.headers.get("authorization");

  // Forward to Python backend
  const response = await fetch(process.env.BACKEND_URL + "/chatkit", {
    method: "POST",
    headers: {
      "Content-Type": "application/octet-stream",
      Authorization: authHeader || "",
    },
    body: await request.arrayBuffer(),
  });

  // Stream response back
  return new Response(response.body, {
    headers: {
      "Content-Type": response.headers.get("Content-Type") || "text/event-stream",
    },
  });
}
```

---

## Error Handling Patterns

### Graceful Degradation
```python
@function_tool(description_override="Get user's recent orders")
async def get_orders(
    ctx: RunContextWrapper[AgentContext],
    limit: int = 5
) -> dict:
    user_id = ctx.context.request_context.get("user_id")

    try:
        orders = await order_service.get_recent(user_id, limit)
        return {
            "orders": [order.to_dict() for order in orders],
            "count": len(orders)
        }
    except ServiceUnavailableError:
        # Graceful degradation
        return {
            "orders": [],
            "count": 0,
            "note": "Order service temporarily unavailable"
        }
    except Exception as e:
        logger.exception(f"Failed to fetch orders for {user_id}")
        return None  # Signal failure to agent
```

### Retry Logic
```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def fetch_with_retry(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()

@function_tool(description_override="Fetch data from external service")
async def fetch_external_data(
    ctx: RunContextWrapper[AgentContext],
    resource_id: str
) -> dict | None:
    try:
        data = await fetch_with_retry(f"{API_URL}/resources/{resource_id}")
        return {"data": data}
    except Exception as e:
        logger.error(f"External fetch failed after retries: {e}")
        return None
```

---

## Testing Patterns

### Unit Test for Tools
```python
# tests/test_tools.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.tools import get_weather

@pytest.mark.asyncio
async def test_get_weather_success():
    # Mock context
    ctx = MagicMock()
    ctx.context = MagicMock()
    ctx.context.request_context = {}

    # Mock API response
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "name": "London",
            "main": {"temp": 15, "humidity": 80},
            "weather": [{"description": "cloudy"}]
        }
        mock_get.return_value.raise_for_status = MagicMock()

        result = await get_weather(ctx, city="London")

        assert result is not None
        assert result["city"] == "London"
        assert result["temperature"] == 15

@pytest.mark.asyncio
async def test_get_weather_failure():
    ctx = MagicMock()
    ctx.context = MagicMock()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Timeout")

        result = await get_weather(ctx, city="London")

        assert result is None
```

### Integration Test for Server
```python
# tests/test_server.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_chatkit_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # ChatKit protocol payload (simplified)
        payload = {
            "type": "message",
            "thread_id": "test-thread",
            "content": "Hello"
        }

        response = await client.post(
            "/chatkit",
            content=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
```
