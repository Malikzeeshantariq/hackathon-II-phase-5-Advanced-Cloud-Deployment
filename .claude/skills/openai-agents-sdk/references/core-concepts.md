# Core Concepts

## Agent

An Agent is an LLM configured with instructions and tools.

### Agent Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Required identifier |
| `instructions` | `str \| Callable` | System prompt (static or dynamic) |
| `model` | `str` | LLM model (`gpt-4.1`, `gpt-5.2`, etc.) |
| `model_settings` | `ModelSettings` | Temperature, top_p, reasoning effort |
| `tools` | `list` | Functions the agent can call |
| `handoffs` | `list[Agent]` | Agents to delegate to |
| `output_type` | `type` | Pydantic model for structured output |
| `input_guardrails` | `list` | Input validation functions |
| `output_guardrails` | `list` | Output validation functions |
| `mcp_servers` | `list` | MCP server connections |

### Basic Agent

```python
from agents import Agent

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    model="gpt-4.1"
)
```

### Agent with Model Settings

```python
from agents import Agent, ModelSettings
from openai.types.shared import Reasoning

agent = Agent(
    name="Reasoner",
    instructions="Think step by step.",
    model="gpt-5.2",
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="high"),
        temperature=0.7
    )
)
```

### Dynamic Instructions

```python
from agents import Agent, RunContextWrapper

def get_instructions(ctx: RunContextWrapper, agent: Agent) -> str:
    return f"Help user {ctx.context.user_name}. Be concise."

agent = Agent(
    name="Dynamic",
    instructions=get_instructions
)
```

### Structured Output

```python
from pydantic import BaseModel
from agents import Agent

class Analysis(BaseModel):
    sentiment: str
    confidence: float
    keywords: list[str]

agent = Agent(
    name="Analyzer",
    instructions="Analyze the sentiment of text.",
    output_type=Analysis
)
```

### Cloning Agents

```python
# Create variant with different instructions
variant = agent.clone(instructions="New instructions here")
```

## Runner

The Runner executes agent workflows.

### Execution Methods

| Method | Type | Use Case |
|--------|------|----------|
| `Runner.run()` | Async | Production async code |
| `Runner.run_sync()` | Sync | Scripts, testing |
| `Runner.run_streamed()` | Async + Stream | Real-time output |

### Agent Loop

```
1. Call LLM with agent config + input
2. If final output → return result
3. If handoff → switch agent, continue
4. If tool calls → execute tools, loop
5. If max_turns exceeded → raise MaxTurnsExceeded
```

### Basic Execution

```python
from agents import Agent, Runner

agent = Agent(name="Bot", instructions="Be helpful.")

# Sync
result = Runner.run_sync(agent, "Hello")
print(result.final_output)

# Async
result = await Runner.run(agent, "Hello")
print(result.final_output)
```

### Streaming

```python
async def stream_response():
    result = Runner.run_streamed(agent, "Tell me a story")

    async for event in result.stream_events():
        if hasattr(event, 'delta'):
            print(event.delta, end='', flush=True)

    # Get final result after stream completes
    final = await result.final_output
    print(final)
```

### RunConfig

```python
from agents import Runner, RunConfig

result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(
        model="gpt-5.2",                    # Override model
        model_settings={"temperature": 0.5}, # Override settings
        tracing_disabled=False,              # Enable tracing
        workflow_name="my_workflow",         # Trace name
        max_turns=10                         # Limit iterations
    )
)
```

## Context (Dependency Injection)

Context passes data/dependencies to tools and agents without sending to LLM.

### Define Context

```python
from dataclasses import dataclass

@dataclass
class AppContext:
    user_id: str
    api_client: any
    logger: any
```

### Use in Tools

```python
from agents import function_tool, RunContextWrapper

@function_tool
async def fetch_user_data(ctx: RunContextWrapper[AppContext]) -> str:
    """Fetch data for current user."""
    user = await ctx.context.api_client.get_user(ctx.context.user_id)
    ctx.context.logger.info(f"Fetched user {user.name}")
    return f"User: {user.name}, Email: {user.email}"
```

### Pass to Runner

```python
context = AppContext(
    user_id="user_123",
    api_client=my_api_client,
    logger=logging.getLogger()
)

result = await Runner.run(
    agent,
    "Get my profile",
    context=context
)
```

### ToolContext (Extended)

Access tool-specific metadata:

```python
from agents.tool_context import ToolContext

@function_tool
def my_tool(ctx: ToolContext[AppContext], param: str) -> str:
    print(f"Tool name: {ctx.tool_name}")
    print(f"Call ID: {ctx.tool_call_id}")
    print(f"Arguments: {ctx.tool_arguments}")
    return "result"
```

## Results

### RunResult Properties

| Property | Type | Description |
|----------|------|-------------|
| `final_output` | `Any` | Last agent's output |
| `last_agent` | `Agent` | Agent that completed |
| `new_items` | `list[RunItem]` | Generated items (messages, tool calls) |
| `input` | `list` | Original input |
| `raw_responses` | `list` | Raw model responses |

### Using Results

```python
result = await Runner.run(agent, "Hello")

# Get output
print(result.final_output)

# Check which agent finished (useful with handoffs)
print(f"Handled by: {result.last_agent.name}")

# Convert to input for next turn
next_input = result.to_input_list()
next_input.append({"role": "user", "content": "Follow-up question"})
result2 = await Runner.run(agent, next_input)
```

### RunItem Types

| Type | Content |
|------|---------|
| `MessageOutputItem` | LLM text messages |
| `ToolCallItem` | Tool invocation requests |
| `ToolCallOutputItem` | Tool results |
| `HandoffCallItem` | Handoff requests |
| `HandoffOutputItem` | Handoff results |
| `ReasoningItem` | Model reasoning (gpt-5.x) |

## Sessions (Conversation Memory)

Sessions automatically manage conversation history across runs.

### SQLite Session (Simple)

```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Memory Bot", instructions="Remember what users tell you.")

# In-memory (lost on restart)
session = SQLiteSession("user_123")

# Persistent (file-based)
session = SQLiteSession("user_123", "conversations.db")

# Usage
result = await Runner.run(agent, "My name is Alice", session=session)
result = await Runner.run(agent, "What's my name?", session=session)
# Output: "Your name is Alice"
```

### SQLAlchemy Session (Production)

```python
from agents.extensions.sessions.sqlalchemy_session import SQLAlchemySession

# PostgreSQL
session = await SQLAlchemySession.from_url(
    "user_123",
    url="postgresql+asyncpg://user:pass@localhost/db"
)

# MySQL
session = await SQLAlchemySession.from_url(
    "user_123",
    url="mysql+aiomysql://user:pass@localhost/db"
)
```

### Session Operations

```python
# Get all history
items = await session.get_items()

# Get recent (limit)
recent = await session.get_items(limit=10)

# Clear conversation
await session.clear_session()

# Remove last exchange (for corrections)
await session.pop_item()  # Remove agent response
await session.pop_item()  # Remove user message
```

### Encrypted Sessions

```python
from agents.extensions.sessions.encrypted_session import EncryptedSession

base_session = SQLiteSession("user_123", "data.db")
secure_session = EncryptedSession(
    base_session,
    encryption_key="your-32-byte-key-here",
    ttl_seconds=3600  # Auto-expire after 1 hour
)
```

## Models

### Default Model

Default is `gpt-4.1`. Override via:

```python
# Environment variable
export OPENAI_DEFAULT_MODEL=gpt-5.2

# RunConfig
result = await Runner.run(agent, "Hi", run_config=RunConfig(model="gpt-5.2"))

# Agent-level
agent = Agent(name="Bot", model="gpt-5.2")
```

### GPT-5.x Settings

```python
from openai.types.shared import Reasoning
from agents import Agent, ModelSettings

agent = Agent(
    name="Thinker",
    model="gpt-5.2",
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="high"),  # low, medium, high
        verbosity="low"
    )
)
```

### Using Non-OpenAI Models (LiteLLM)

```bash
pip install "openai-agents[litellm]"
```

```python
from agents import Agent

# Anthropic Claude
agent = Agent(
    name="Claude Bot",
    model="litellm/anthropic/claude-3-5-sonnet-20240620"
)

# Google Gemini
agent = Agent(
    name="Gemini Bot",
    model="litellm/gemini/gemini-2.5-flash-preview-04-17"
)

# Local Ollama
agent = Agent(
    name="Local Bot",
    model="litellm/ollama/llama3"
)
```

### Tracing with Non-OpenAI Models

```python
from agents import set_tracing_export_api_key
import os

# Set OpenAI key for tracing only
set_tracing_export_api_key(os.environ["OPENAI_API_KEY"])

# Or disable tracing
from agents import set_tracing_disabled
set_tracing_disabled(True)
```

## Configuration

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | API authentication |
| `OPENAI_DEFAULT_MODEL` | Default model |
| `OPENAI_AGENTS_DISABLE_TRACING` | Set to `1` to disable |
| `OPENAI_AGENTS_DONT_LOG_MODEL_DATA` | Don't log LLM I/O |
| `OPENAI_AGENTS_DONT_LOG_TOOL_DATA` | Don't log tool I/O |

### Programmatic Configuration

```python
from agents import (
    set_default_openai_key,
    set_default_openai_client,
    set_default_openai_api,
    set_tracing_disabled,
    enable_verbose_stdout_logging
)

# Set API key
set_default_openai_key("sk-...")

# Use custom client
from openai import AsyncOpenAI
client = AsyncOpenAI(base_url="https://custom-endpoint.com/v1")
set_default_openai_client(client)

# Use Chat Completions API instead of Responses
set_default_openai_api("chat_completions")

# Enable debug logging
enable_verbose_stdout_logging()
```
