---
name: openai-agents-sdk
description: |
  Build AI agents using OpenAI Agents SDK - from hello world to production systems.
  This skill should be used when users want to create agents, multi-agent workflows,
  implement tools, handoffs, guardrails, sessions, or any agentic AI application
  using the OpenAI Agents SDK (Python).
---

# OpenAI Agents SDK

Build AI agents from simple hello world examples to professional production systems.

## Before Implementation

| Source | Gather |
|--------|--------|
| **Codebase** | Existing patterns, dependencies, Python version (3.9+ required) |
| **Conversation** | User's specific agent requirements, use case, complexity level |
| **Skill References** | Patterns from `references/` (core concepts, tools, patterns, examples) |
| **User Guidelines** | Project conventions, error handling preferences |

## Quick Start

```bash
# Install
pip install openai-agents

# Set API key
export OPENAI_API_KEY=sk-...
```

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are helpful.")
result = Runner.run_sync(agent, "Hello!")
print(result.final_output)
```

## Core Primitives

| Primitive | Purpose | Key Parameters |
|-----------|---------|----------------|
| **Agent** | LLM with instructions + tools | `name`, `instructions`, `tools`, `handoffs`, `output_type` |
| **Runner** | Executes agent workflows | `run()`, `run_sync()`, `run_streamed()` |
| **Tools** | Functions agents can call | `@function_tool` decorator |
| **Handoffs** | Transfer between agents | `handoffs=[agent1, agent2]` |
| **Guardrails** | Input/output validation | `@input_guardrail`, `@output_guardrail` |
| **Sessions** | Conversation persistence | `SQLiteSession`, `SQLAlchemySession` |

## Implementation Workflow

```
1. Define Agent(s) → 2. Add Tools → 3. Configure Handoffs → 4. Add Guardrails → 5. Run with Runner
```

### Step 1: Define Agent

```python
from agents import Agent

agent = Agent(
    name="CustomerSupport",
    instructions="You help customers with their questions.",
    model="gpt-4.1",  # or gpt-5.2 for reasoning
)
```

### Step 2: Add Tools

```python
from agents import function_tool

@function_tool
def get_order_status(order_id: str) -> str:
    """Get the status of an order by ID."""
    return f"Order {order_id} is shipped"

agent = Agent(
    name="Support",
    instructions="Help with order inquiries.",
    tools=[get_order_status]
)
```

### Step 3: Configure Handoffs (Multi-Agent)

```python
billing_agent = Agent(name="Billing", instructions="Handle billing questions.")
technical_agent = Agent(name="Technical", instructions="Handle technical issues.")

triage_agent = Agent(
    name="Triage",
    instructions="Route to appropriate specialist.",
    handoffs=[billing_agent, technical_agent]
)
```

### Step 4: Add Guardrails

```python
from agents import input_guardrail, GuardrailFunctionOutput

@input_guardrail
async def block_harmful(ctx, agent, input):
    # Check input safety
    is_harmful = "harmful" in str(input).lower()
    return GuardrailFunctionOutput(tripwire_triggered=is_harmful)

agent = Agent(
    name="Safe Agent",
    input_guardrails=[block_harmful]
)
```

### Step 5: Run

```python
from agents import Runner

# Sync
result = Runner.run_sync(agent, "What's my order status?")

# Async
result = await Runner.run(agent, "What's my order status?")

# Streaming
async for event in Runner.run_streamed(agent, "Hello").stream_events():
    print(event)
```

## Clarifications to Gather

Before implementing, clarify:

| Question | Why It Matters |
|----------|----------------|
| Single or multi-agent? | Determines architecture complexity |
| What tools needed? | Functions, web search, file search, code interpreter |
| Need conversation memory? | Determines session implementation |
| Production or prototype? | Affects error handling, tracing, guardrails |
| Voice/realtime needed? | Requires additional voice dependencies |

## Pattern Selection

| Use Case | Pattern | Reference |
|----------|---------|-----------|
| Simple Q&A | Single agent | `references/examples.md#hello-world` |
| Specialized routing | Handoffs (decentralized) | `references/patterns.md#handoffs` |
| Orchestrator control | Manager pattern | `references/patterns.md#manager` |
| Parallel tasks | Async gather | `references/patterns.md#parallel` |
| Production system | Full stack | `references/production-guide.md` |

## Common Tasks

### Structured Output

```python
from pydantic import BaseModel

class OrderInfo(BaseModel):
    order_id: str
    status: str
    estimated_delivery: str

agent = Agent(
    name="OrderAgent",
    instructions="Extract order information.",
    output_type=OrderInfo
)
```

### Context/Dependency Injection

```python
from dataclasses import dataclass
from agents import RunContextWrapper

@dataclass
class AppContext:
    user_id: str
    db_connection: any

@function_tool
async def get_user_data(ctx: RunContextWrapper[AppContext]) -> str:
    return f"Data for user {ctx.context.user_id}"

result = await Runner.run(agent, "Get my data", context=AppContext(user_id="123", db_connection=db))
```

### Sessions (Conversation Memory)

```python
from agents import SQLiteSession

session = SQLiteSession("user_123", "conversations.db")

# Turn 1
result = await Runner.run(agent, "My name is Alice", session=session)

# Turn 2 - Agent remembers
result = await Runner.run(agent, "What's my name?", session=session)
```

### Using Non-OpenAI Models

```python
# Install: pip install "openai-agents[litellm]"
agent = Agent(
    name="Claude Agent",
    model="litellm/anthropic/claude-3-5-sonnet-20240620"
)
```

## Reference Files

| File | Content |
|------|---------|
| `references/core-concepts.md` | Agent, Runner, Context, Results details |
| `references/tools-reference.md` | Function tools, hosted tools, MCP |
| `references/patterns.md` | Multi-agent patterns, orchestration |
| `references/production-guide.md` | Guardrails, tracing, sessions, deployment |
| `references/examples.md` | Hello world to advanced examples |

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Do Instead |
|--------------|--------------|------------|
| Giant monolithic agent | Hard to debug, maintain | Split into specialized agents with handoffs |
| No guardrails in production | Security/safety risks | Add input/output guardrails |
| Ignoring tracing | Can't debug issues | Enable tracing, use OpenAI dashboard |
| Manual conversation management | Error-prone, complex | Use Sessions |
| Hardcoded API keys | Security risk | Use environment variables |

## Checklist

- [ ] Python 3.9+ installed
- [ ] `openai-agents` package installed
- [ ] `OPENAI_API_KEY` environment variable set
- [ ] Agent(s) defined with clear instructions
- [ ] Tools implemented with proper docstrings
- [ ] Handoffs configured (if multi-agent)
- [ ] Guardrails added (for production)
- [ ] Sessions configured (if multi-turn)
- [ ] Tracing enabled for debugging
- [ ] Error handling implemented
