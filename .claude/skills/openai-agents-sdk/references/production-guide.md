# Production Guide

## Production Checklist

- [ ] Guardrails configured (input + output)
- [ ] Tracing enabled with proper workflow names
- [ ] Sessions configured for conversation persistence
- [ ] Error handling implemented
- [ ] Rate limiting considered
- [ ] Secrets in environment variables
- [ ] Logging configured
- [ ] Monitoring/alerting set up
- [ ] Cost controls in place

## Guardrails

### Input Guardrails

Validate user input before agent execution.

```python
from pydantic import BaseModel
from agents import (
    Agent, Runner, GuardrailFunctionOutput,
    RunContextWrapper, TResponseInputItem,
    input_guardrail, InputGuardrailTripwireTriggered
)

class SafetyCheck(BaseModel):
    is_safe: bool
    reason: str

safety_checker = Agent(
    name="SafetyChecker",
    instructions="Check if input is safe. Flag harmful, illegal, or inappropriate content.",
    output_type=SafetyCheck
)

@input_guardrail
async def safety_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(safety_checker, input, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_safe
    )

# Apply to agent
agent = Agent(
    name="Assistant",
    instructions="Help users with their questions.",
    input_guardrails=[safety_guardrail]
)

# Handle tripwire
async def safe_run(agent, input):
    try:
        return await Runner.run(agent, input)
    except InputGuardrailTripwireTriggered as e:
        return "I cannot help with that request."
```

### Output Guardrails

Validate agent output before returning to user.

```python
from agents import (
    Agent, Runner, GuardrailFunctionOutput,
    output_guardrail, OutputGuardrailTripwireTriggered
)

class OutputCheck(BaseModel):
    contains_pii: bool
    contains_secrets: bool

pii_checker = Agent(
    name="PIIChecker",
    instructions="Check if output contains PII (emails, phones, SSN) or secrets.",
    output_type=OutputCheck
)

@output_guardrail
async def pii_guardrail(ctx, agent, output) -> GuardrailFunctionOutput:
    result = await Runner.run(pii_checker, str(output), context=ctx.context)
    check = result.final_output

    return GuardrailFunctionOutput(
        output_info=check,
        tripwire_triggered=check.contains_pii or check.contains_secrets
    )

agent = Agent(
    name="DataBot",
    instructions="Help with data queries.",
    output_guardrails=[pii_guardrail]
)
```

### Tool Guardrails

Validate tool inputs/outputs.

```python
import json
from agents import (
    function_tool,
    tool_input_guardrail,
    tool_output_guardrail,
    ToolGuardrailFunctionOutput
)

@tool_input_guardrail
def validate_tool_input(data):
    args = json.loads(data.context.tool_arguments or "{}")

    # Block if contains sensitive data
    if "password" in json.dumps(args).lower():
        return ToolGuardrailFunctionOutput.reject_content(
            "Cannot process requests containing passwords"
        )

    return ToolGuardrailFunctionOutput.allow()

@tool_output_guardrail
def sanitize_tool_output(data):
    output = str(data.output or "")

    # Redact sensitive patterns
    if "sk-" in output or "api_key" in output.lower():
        return ToolGuardrailFunctionOutput.reject_content(
            "Output contained sensitive data and was blocked"
        )

    return ToolGuardrailFunctionOutput.allow()

@function_tool(
    tool_input_guardrails=[validate_tool_input],
    tool_output_guardrails=[sanitize_tool_output]
)
def query_database(query: str) -> str:
    """Execute a database query."""
    return execute_query(query)
```

### Guardrail Execution Modes

```python
# Parallel (default) - guardrail runs alongside agent
@input_guardrail
async def fast_guardrail(ctx, agent, input):
    # Runs in parallel with agent for lower latency
    pass

# Blocking - guardrail must complete before agent starts
@input_guardrail(run_in_parallel=False)
async def blocking_guardrail(ctx, agent, input):
    # Saves tokens if tripwire triggers (agent never runs)
    pass
```

## Tracing

### Enable Tracing

Tracing is enabled by default. Configure via:

```python
from agents import Runner, RunConfig

result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(
        workflow_name="customer_support",  # Name in dashboard
        trace_id="trace_custom123",        # Custom trace ID
        group_id="session_abc",            # Group related traces
        tracing_disabled=False             # Ensure enabled
    )
)
```

### Custom Traces

Group multiple runs into single trace:

```python
from agents import Agent, Runner, trace

async def support_workflow(user_input: str):
    with trace("Support Workflow"):
        # All runs grouped under one trace
        classification = await Runner.run(classifier, user_input)
        response = await Runner.run(responder, user_input)
        followup = await Runner.run(followup_agent, response.final_output)

    return followup.final_output
```

### Custom Spans

Track custom operations:

```python
from agents import custom_span

async def my_workflow():
    with custom_span("database_query"):
        data = await fetch_from_database()

    with custom_span("external_api"):
        enriched = await call_external_api(data)

    return enriched
```

### Sensitive Data Control

```python
from agents import RunConfig

# Disable sensitive data in traces
result = await Runner.run(
    agent,
    "Process this PII",
    run_config=RunConfig(
        trace_include_sensitive_data=False
    )
)

# Or via environment variable
# OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA=0
```

### External Trace Processors

```python
from agents import add_trace_processor
from my_observability import CustomProcessor

# Add alongside OpenAI tracing
add_trace_processor(CustomProcessor())

# Supported integrations:
# - Weights & Biases
# - Arize Phoenix
# - MLflow
# - Braintrust
# - Pydantic Logfire
# - AgentOps
# - LangSmith
# - Langfuse
```

## Sessions (Production)

### SQLAlchemy (Recommended for Production)

```python
from agents.extensions.sessions.sqlalchemy_session import SQLAlchemySession

# PostgreSQL
session = await SQLAlchemySession.from_url(
    session_id="user_123",
    url="postgresql+asyncpg://user:pass@localhost:5432/agents_db"
)

# With connection pool settings
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost:5432/agents_db",
    pool_size=20,
    max_overflow=10
)

session = SQLAlchemySession(
    session_id="user_123",
    engine=engine
)
```

### Redis Sessions

```bash
pip install "openai-agents[redis]"
```

```python
from agents.extensions.sessions.redis_session import RedisSession

session = RedisSession(
    session_id="user_123",
    redis_url="redis://localhost:6379",
    ttl_seconds=3600  # Auto-expire after 1 hour
)
```

### Encrypted Sessions

```python
from agents import SQLiteSession
from agents.extensions.sessions.encrypted_session import EncryptedSession

base = SQLiteSession("user_123", "data.db")
session = EncryptedSession(
    base,
    encryption_key="32-byte-encryption-key-here!!!!",  # Must be 32 bytes
    ttl_seconds=7200
)
```

### Session Management

```python
# Cleanup old sessions (background job)
async def cleanup_sessions():
    cutoff = datetime.now() - timedelta(days=30)
    await session_store.delete_older_than(cutoff)

# Handle session not found
async def get_or_create_session(user_id: str):
    try:
        return await SQLAlchemySession.from_url(user_id, db_url)
    except SessionNotFound:
        session = await SQLAlchemySession.from_url(user_id, db_url)
        return session
```

## Error Handling

### Exception Hierarchy

```python
from agents import (
    AgentsException,           # Base exception
    MaxTurnsExceeded,          # Too many iterations
    ModelBehaviorError,        # Invalid model output
    UserError,                 # SDK misuse
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered
)

async def robust_run(agent, input):
    try:
        return await Runner.run(agent, input)

    except InputGuardrailTripwireTriggered:
        return {"error": "Input rejected by safety filters"}

    except OutputGuardrailTripwireTriggered:
        return {"error": "Output blocked by safety filters"}

    except MaxTurnsExceeded:
        return {"error": "Agent took too long to respond"}

    except ModelBehaviorError as e:
        logger.error(f"Model error: {e}")
        return {"error": "AI model returned invalid response"}

    except AgentsException as e:
        logger.error(f"Agent error: {e}")
        return {"error": "An error occurred processing your request"}
```

### Tool Error Handling

```python
@function_tool(failure_error_function=handle_tool_error)
def risky_tool(param: str) -> str:
    """Tool that might fail."""
    try:
        return perform_operation(param)
    except OperationError as e:
        raise ToolExecutionError(f"Operation failed: {e}")

def handle_tool_error(error: Exception, ctx) -> str:
    logger.error(f"Tool failed: {error}")
    return f"Tool encountered an error: {str(error)}"
```

### Retry Logic

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def run_with_retry(agent, input):
    return await Runner.run(agent, input)
```

## Cost Control

### Limit Turns

```python
result = await Runner.run(
    agent,
    input,
    run_config=RunConfig(max_turns=5)  # Limit iterations
)
```

### Model Selection Strategy

```python
# Use cheaper models for simple tasks
classifier = Agent(name="Classifier", model="gpt-4.1-mini")

# Use powerful models for complex tasks
reasoner = Agent(name="Reasoner", model="gpt-5.2")

# Dynamic model selection
def select_model(complexity: str) -> str:
    return {
        "low": "gpt-4.1-mini",
        "medium": "gpt-4.1",
        "high": "gpt-5.2"
    }.get(complexity, "gpt-4.1")
```

### Context Window Management

```python
def call_model_input_filter(data):
    """Trim old messages to manage context."""
    messages = data.model_data.input

    # Keep only recent messages
    if len(messages) > 20:
        messages = messages[-10:]

    return ModelInputData(
        input=messages,
        instructions=data.model_data.instructions
    )

result = await Runner.run(
    agent,
    input,
    run_config=RunConfig(call_model_input_filter=call_model_input_filter)
)
```

## Logging

### Enable Verbose Logging

```python
from agents import enable_verbose_stdout_logging

enable_verbose_stdout_logging()
```

### Custom Logging

```python
import logging

# Configure agents logger
logger = logging.getLogger("openai.agents")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("agents.log")
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)
```

### Sensitive Data Protection

```bash
# Don't log model inputs/outputs
export OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1

# Don't log tool inputs/outputs
export OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1
```

## Deployment Patterns

### Async Web Server (FastAPI)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents import Agent, Runner

app = FastAPI()
agent = Agent(name="API Bot", instructions="Help with API queries.")

class Query(BaseModel):
    message: str
    user_id: str

@app.post("/chat")
async def chat(query: Query):
    try:
        session = await get_session(query.user_id)
        result = await Runner.run(agent, query.message, session=session)
        return {"response": result.final_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Background Processing (Celery)

```python
from celery import Celery
from agents import Agent, Runner

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def process_document(doc_id: str):
    agent = Agent(name="Processor", instructions="Process documents.")
    result = Runner.run_sync(agent, f"Process document {doc_id}")
    return result.final_output
```

### Long-Running Workflows (Temporal)

```python
# The SDK supports Temporal for durable workflows
# See: https://openai.github.io/openai-agents-python/running_agents/#long-running-agents

from temporalio import workflow
from agents import Agent, Runner

@workflow.defn
class AgentWorkflow:
    @workflow.run
    async def run(self, input: str) -> str:
        agent = Agent(name="Worker", instructions="Process tasks.")
        result = await Runner.run(agent, input)
        return result.final_output
```

## Security Best Practices

### API Key Management

```python
import os

# Never hardcode keys
# BAD: api_key = "sk-..."
# GOOD:
api_key = os.environ["OPENAI_API_KEY"]

# Or use secret manager
from your_secret_manager import get_secret
api_key = get_secret("openai-api-key")
```

### Input Sanitization

```python
def sanitize_input(user_input: str) -> str:
    # Remove potential injection attempts
    sanitized = user_input.strip()

    # Limit length
    if len(sanitized) > 10000:
        sanitized = sanitized[:10000]

    return sanitized

result = await Runner.run(agent, sanitize_input(user_input))
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, query: Query):
    # Rate limited endpoint
    pass
```

### Audit Logging

```python
async def audited_run(agent, input, user_id: str):
    audit_log.info(f"User {user_id} started agent run", extra={
        "user_id": user_id,
        "agent": agent.name,
        "input_length": len(str(input))
    })

    result = await Runner.run(agent, input)

    audit_log.info(f"User {user_id} completed agent run", extra={
        "user_id": user_id,
        "agent": result.last_agent.name,
        "output_length": len(str(result.final_output))
    })

    return result
```
