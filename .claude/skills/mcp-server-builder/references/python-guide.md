# Python MCP Server Guide

Complete patterns for building MCP servers with Python and FastMCP.

## Installation

```bash
# Using uv (recommended)
uv add "mcp[cli]" httpx

# Using pip
pip install "mcp[cli]" httpx
```

## Server Initialization

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server-name")

# Run with stdio transport (default)
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## Registering Tools

### Basic Tool
```python
@mcp.tool()
async def tool_name(param1: str, param2: int = 10) -> str:
    """Clear description of what this tool does.

    Args:
        param1: What this parameter is for
        param2: Optional numeric param with default
    """
    result = await do_something(param1, param2)
    return str(result)
```

FastMCP automatically:
- Infers JSON Schema from type hints
- Uses docstring for description
- Parses Args section for parameter descriptions

### Tool with Complex Types
```python
from typing import Optional
from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    status: Optional[str] = Field(None, description="Filter by status")
    date_from: Optional[str] = Field(None, description="ISO date string")
    date_to: Optional[str] = Field(None, description="ISO date string")


@mcp.tool()
async def search_records(
    query: str,
    filters: Optional[SearchFilters] = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search database records with filters.

    Args:
        query: Search query string
        filters: Optional search filters
        limit: Maximum results (1-100)
        offset: Pagination offset
    """
    results = await search_database(query, filters, limit, offset)
    return {"results": results, "count": len(results)}
```

### Tool with Error Handling
```python
import httpx


@mcp.tool()
async def fetch_data(endpoint: str) -> str:
    """Fetch data from external API.

    Args:
        endpoint: API endpoint URL
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, timeout=30.0)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        raise ValueError(f"API error: {e.response.status_code}")
    except httpx.RequestError as e:
        raise ValueError(f"Request failed: {str(e)}")
```

### Tool with Context
```python
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession


@mcp.tool()
async def long_task(
    input_data: str,
    ctx: Context[ServerSession, None],
) -> str:
    """Perform a long-running task with progress reporting.

    Args:
        input_data: Data to process
    """
    await ctx.info("Starting task...")

    for i in range(10):
        await ctx.report_progress(progress=i, total=10)
        await process_chunk(input_data, i)

    await ctx.info("Task complete!")
    return "Done"
```

## Registering Resources

### Static Resources
```python
@mcp.resource("config://app/settings")
async def get_settings() -> str:
    """Application configuration settings."""
    settings = await load_settings()
    return json.dumps(settings, indent=2)


@mcp.resource("file://logs/latest")
async def get_latest_logs() -> str:
    """Most recent application logs."""
    return await read_latest_logs()
```

### Resource Templates
```python
@mcp.resource("file:///{path}")
async def read_file(path: str) -> str:
    """Read a file from the project directory.

    Args:
        path: Relative file path
    """
    # Validate path to prevent directory traversal
    safe_path = Path(path).resolve()
    if not safe_path.is_relative_to(PROJECT_ROOT):
        raise ValueError("Access denied: path outside project")

    return safe_path.read_text()


@mcp.resource("db://users/{user_id}")
async def get_user(user_id: str) -> str:
    """Fetch user record by ID.

    Args:
        user_id: User identifier
    """
    user = await database.get_user(user_id)
    if not user:
        raise ValueError(f"User not found: {user_id}")
    return json.dumps(user.dict())
```

## Registering Prompts

```python
@mcp.prompt()
async def code_review(code: str, language: str = "python") -> str:
    """Review code for quality and best practices.

    Args:
        code: The code to review
        language: Programming language
    """
    return f"""Please review this {language} code for quality, best practices, and potential issues:

```{language}
{code}
```

Focus on:
1. Code quality and readability
2. Potential bugs or edge cases
3. Performance considerations
4. Security issues
"""
```

## Structured Output

FastMCP supports automatic result validation:

```python
from pydantic import BaseModel


class WeatherResult(BaseModel):
    temperature: float
    conditions: str
    humidity: int


@mcp.tool()
async def get_weather(location: str) -> WeatherResult:
    """Get weather for a location.

    Args:
        location: City name or coordinates
    """
    data = await fetch_weather_api(location)
    return WeatherResult(
        temperature=data["temp"],
        conditions=data["conditions"],
        humidity=data["humidity"],
    )
```

## Lifespan Management

Handle startup/shutdown with async context managers:

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator
from dataclasses import dataclass


@dataclass
class AppContext:
    db: Database
    cache: Cache


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle."""
    # Startup
    db = await Database.connect()
    cache = await Cache.connect()

    try:
        yield AppContext(db=db, cache=cache)
    finally:
        # Shutdown
        await cache.disconnect()
        await db.disconnect()


mcp = FastMCP("my-server", lifespan=app_lifespan)


@mcp.tool()
async def query_data(
    sql: str,
    ctx: Context[ServerSession, AppContext],
) -> str:
    """Execute database query.

    Args:
        sql: SQL query to execute
    """
    db = ctx.request_context.lifespan_context.db
    results = await db.execute(sql)
    return json.dumps(results)
```

## HTTP Transport

For remote servers:

```python
mcp = FastMCP("http-server")

# Run with HTTP transport
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=3000,
    )
```

### With Authentication
```python
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl

mcp = FastMCP(
    name="secure-server",
    host="localhost",
    port=3000,
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://auth.example.com/"),
        required_scopes=["mcp:tools"],
        resource_server_url=AnyHttpUrl("http://localhost:3000"),
    ),
)
```

## Logging Best Practices

**CRITICAL: Never use print() in stdio servers!**

```python
# ❌ BAD - Breaks JSON-RPC protocol
print("Processing request")

# ✅ GOOD - Use logging module
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Processing request")

# ✅ ALSO GOOD - Write to stderr
import sys

print("Debug info", file=sys.stderr)
```

## Complete Server Example

```python
#!/usr/bin/env python3
"""Complete MCP server example."""
import json
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("complete-example")


# Tool: Calculator
@mcp.tool()
async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Math expression (e.g., "2 + 2 * 3")
    """
    try:
        # Use ast.literal_eval for safety in production
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


# Tool: String operations
@mcp.tool()
async def text_transform(
    text: str,
    operation: str = "upper",
) -> str:
    """Transform text with various operations.

    Args:
        text: Input text to transform
        operation: Operation: upper, lower, title, reverse
    """
    operations = {
        "upper": str.upper,
        "lower": str.lower,
        "title": str.title,
        "reverse": lambda s: s[::-1],
    }

    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")

    return operations[operation](text)


# Resource: Server info
@mcp.resource("info://server")
async def server_info() -> str:
    """Current server information."""
    import time

    return json.dumps(
        {
            "name": "complete-example",
            "version": "1.0.0",
            "timestamp": time.time(),
        },
        indent=2,
    )


# Prompt: Analysis template
@mcp.prompt()
async def analyze_text(text: str) -> str:
    """Analyze text for various properties.

    Args:
        text: Text to analyze
    """
    return f"""Please analyze the following text:

{text}

Provide analysis of:
1. Sentiment (positive/negative/neutral)
2. Key themes
3. Writing style
4. Suggestions for improvement
"""


def main():
    logger.info("Starting MCP server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

## Testing

```bash
# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run server.py

# Or run directly
uv run server.py
```
