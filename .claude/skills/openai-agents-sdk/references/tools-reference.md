# Tools Reference

Tools allow agents to perform actions and retrieve information.

## Tool Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Function Tools** | Custom Python functions | `@function_tool` decorated functions |
| **Hosted Tools** | OpenAI-managed tools | Web search, file search, code interpreter |
| **MCP Tools** | Model Context Protocol servers | Filesystem, Git, databases |
| **Agents as Tools** | Other agents callable as tools | Sub-agents for specific tasks |

## Function Tools

### Basic Function Tool

```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The name of the city to get weather for.
    """
    # Implementation
    return f"Weather in {city}: Sunny, 72°F"
```

### Async Function Tool

```python
@function_tool
async def fetch_data(url: str) -> str:
    """Fetch data from a URL.

    Args:
        url: The URL to fetch data from.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

### With Context

```python
from agents import function_tool, RunContextWrapper

@function_tool
async def get_user_orders(ctx: RunContextWrapper[AppContext], limit: int = 10) -> str:
    """Get recent orders for the current user.

    Args:
        limit: Maximum number of orders to return.
    """
    orders = await ctx.context.db.get_orders(
        user_id=ctx.context.user_id,
        limit=limit
    )
    return json.dumps([o.dict() for o in orders])
```

### Custom Tool Name

```python
@function_tool(name_override="search_products")
def find_products(query: str, category: str = None) -> str:
    """Search for products in the catalog."""
    pass
```

### Return Types

```python
from agents import function_tool, ToolOutputText, ToolOutputImage, ToolOutputFileContent

# Text (default)
@function_tool
def text_tool() -> str:
    return "Plain text result"

# Explicit text
@function_tool
def explicit_text() -> ToolOutputText:
    return ToolOutputText(text="Formatted text")

# Image (base64)
@function_tool
def generate_chart() -> ToolOutputImage:
    img_bytes = create_chart()
    return ToolOutputImage(
        data=base64.b64encode(img_bytes).decode(),
        media_type="image/png"
    )

# File
@function_tool
def generate_report() -> ToolOutputFileContent:
    return ToolOutputFileContent(
        filename="report.csv",
        data=csv_content.encode(),
        media_type="text/csv"
    )
```

### Error Handling

```python
@function_tool(failure_error_function=lambda e, ctx: f"Tool failed: {str(e)}")
def risky_operation(param: str) -> str:
    """Operation that might fail."""
    if not valid(param):
        raise ValueError("Invalid parameter")
    return "Success"
```

### Conditional Enabling

```python
def check_feature_flag(ctx, agent):
    return ctx.context.features.is_enabled("advanced_search")

@function_tool(is_enabled=check_feature_flag)
def advanced_search(query: str) -> str:
    """Advanced search (feature-flagged)."""
    pass
```

### Pydantic Models as Parameters

```python
from pydantic import BaseModel

class SearchParams(BaseModel):
    query: str
    filters: dict = {}
    limit: int = 10

@function_tool
def search(params: SearchParams) -> str:
    """Search with structured parameters."""
    return f"Searching for {params.query} with {params.filters}"
```

## Hosted Tools (OpenAI)

Available when using `OpenAIResponsesModel` (default).

### Web Search

```python
from agents import Agent
from agents.tools import WebSearchTool

agent = Agent(
    name="Researcher",
    instructions="Research topics using web search.",
    tools=[WebSearchTool()]
)
```

### File Search (Vector Store)

```python
from agents.tools import FileSearchTool

# Create vector store first via OpenAI API
agent = Agent(
    name="DocBot",
    instructions="Answer questions from uploaded documents.",
    tools=[FileSearchTool(vector_store_ids=["vs_abc123"])]
)
```

### Code Interpreter

```python
from agents.tools import CodeInterpreterTool

agent = Agent(
    name="Coder",
    instructions="Execute Python code to solve problems.",
    tools=[CodeInterpreterTool()]
)
```

### Image Generation

```python
from agents.tools import ImageGenerationTool

agent = Agent(
    name="Artist",
    instructions="Generate images based on descriptions.",
    tools=[ImageGenerationTool()]
)
```

### Hosted MCP Tool

```python
from agents.tools import HostedMCPTool

agent = Agent(
    name="GitBot",
    tools=[
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "gitmcp",
                "server_url": "https://gitmcp.io/openai/codex",
                "require_approval": "never"
            }
        )
    ]
)
```

## Local Runtime Tools

### Computer Tool (GUI Automation)

```python
from agents.tools import ComputerTool

# Requires implementing Computer or AsyncComputer interface
agent = Agent(
    name="Automator",
    tools=[ComputerTool(computer=my_computer_impl)]
)
```

### Shell Tool

```python
from agents.tools import LocalShellTool

agent = Agent(
    name="Shell",
    instructions="Execute shell commands.",
    tools=[LocalShellTool()]  # Be careful with security!
)
```

## MCP (Model Context Protocol)

### Stdio MCP Server

```python
from agents import Agent
from agents.mcp import MCPServerStdio

# Local MCP server via subprocess
server = MCPServerStdio(
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
)

agent = Agent(
    name="FileBot",
    mcp_servers=[server]
)

# Use with context manager
async with server:
    result = await Runner.run(agent, "List files in the directory")
```

### HTTP MCP Server

```python
from agents.mcp import MCPServerStreamableHttp

server = MCPServerStreamableHttp(
    url="https://my-mcp-server.com/mcp",
    headers={"Authorization": "Bearer token"}
)

agent = Agent(
    name="RemoteBot",
    mcp_servers=[server]
)
```

### Tool Filtering

```python
from agents.mcp import create_static_tool_filter

# Only allow specific tools
server = MCPServerStdio(
    params={"command": "my-server"},
    tool_filter=create_static_tool_filter(
        allowed_tool_names=["read_file", "list_directory"]
    )
)

# Block specific tools
server = MCPServerStdio(
    params={"command": "my-server"},
    tool_filter=create_static_tool_filter(
        blocked_tool_names=["delete_file", "write_file"]
    )
)
```

## Agents as Tools

Convert agents into callable tools for orchestration.

### Basic Agent Tool

```python
from agents import Agent

# Specialist agent
translator = Agent(
    name="Translator",
    instructions="Translate text to Spanish."
)

# Orchestrator uses translator as tool
orchestrator = Agent(
    name="Orchestrator",
    instructions="Help users with various tasks.",
    tools=[
        translator.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate text to Spanish"
        )
    ]
)
```

### With Custom Output Extraction

```python
def extract_translation(output):
    # Custom processing of sub-agent output
    return output.strip().upper()

orchestrator = Agent(
    name="Orchestrator",
    tools=[
        translator.as_tool(
            tool_name="translate",
            tool_description="Translate text",
            custom_output_extractor=extract_translation
        )
    ]
)
```

## Tool Choice Control

Control how agents use tools.

```python
from agents import Agent

# Auto (default): LLM decides
agent = Agent(name="Bot", tools=[my_tool], tool_choice="auto")

# Required: Must use a tool
agent = Agent(name="Bot", tools=[my_tool], tool_choice="required")

# None: Cannot use tools
agent = Agent(name="Bot", tools=[my_tool], tool_choice="none")

# Specific: Force specific tool
agent = Agent(name="Bot", tools=[my_tool], tool_choice="my_tool_name")
```

## Tool Use Behavior

Control what happens after tool execution.

```python
from agents import Agent, StopAtTools

# Default: LLM processes tool results
agent = Agent(name="Bot", tool_use_behavior="run_llm_again")

# Stop after first tool
agent = Agent(name="Bot", tool_use_behavior="stop_on_first_tool")

# Stop on specific tools
agent = Agent(
    name="Bot",
    tool_use_behavior=StopAtTools(stop_at=["final_answer", "submit"])
)
```

## Manual FunctionTool

For advanced cases, create tools manually:

```python
from agents import FunctionTool

async def my_handler(ctx, args_json: str) -> str:
    args = json.loads(args_json)
    return f"Processed: {args}"

tool = FunctionTool(
    name="custom_tool",
    description="A custom tool with manual schema",
    params_json_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "default": 10}
        },
        "required": ["query"]
    },
    on_invoke_tool=my_handler
)

agent = Agent(name="Bot", tools=[tool])
```

## Docstring Parsing

The SDK auto-parses docstrings for parameter descriptions.

### Google Style (Recommended)

```python
@function_tool
def search(query: str, limit: int = 10) -> str:
    """Search for items.

    Args:
        query: The search query string.
        limit: Maximum results to return.

    Returns:
        JSON string of search results.
    """
    pass
```

### Sphinx Style

```python
@function_tool
def search(query: str, limit: int = 10) -> str:
    """Search for items.

    :param query: The search query string.
    :param limit: Maximum results to return.
    :returns: JSON string of search results.
    """
    pass
```

### Disable Docstring Parsing

```python
@function_tool(use_docstring_info=False)
def my_tool(x: str) -> str:
    """This docstring won't be used for schema."""
    pass
```
