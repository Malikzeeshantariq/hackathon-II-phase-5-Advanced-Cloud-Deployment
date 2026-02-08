# Quickstart: Todo AI Chatbot (Phase 3)

**Branch**: `001-todo-ai-chatbot` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)

## Overview

Quick setup guide for developing and running the AI-powered conversational interface for the Todo application.

## Prerequisites

- Python 3.11+ with pip
- Node.js 18+ with npm/yarn
- PostgreSQL (Neon Serverless recommended)
- Better Auth configured (Phase 2)
- OpenAI API key or compatible endpoint
- MCP SDK installed

## Environment Setup

### Backend (Python/FastAPI)

```bash
# Navigate to backend directory
cd backend/

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BETTER_AUTH_SECRET="your-secret-key"
export DATABASE_URL="postgresql://user:pass@host/db"
export CORS_ORIGINS="http://localhost:3000"
export OPENAI_API_KEY="your-openai-api-key"
```

### Frontend (Next.js)

```bash
# Navigate to frontend directory
cd frontend/

# Install dependencies
npm install

# Set environment variables
export NEXT_PUBLIC_API_URL="http://localhost:8000"
export NEXT_PUBLIC_BETTER_AUTH_URL="http://localhost:3000"
```

## Running the Application

### 1. Start the Database

Ensure PostgreSQL is running and create the required tables:

```bash
# Run migrations to create Phase 3 tables
python -m alembic upgrade head
```

### 2. Start the Backend

```bash
# From backend directory
uvicorn app.main:app --reload --port 8000
```

### 3. Start the MCP Server

```bash
# From backend directory
python -m app.mcp.server
```

### 4. Start the Frontend

```bash
# From frontend directory
npm run dev
```

## API Endpoints

### Chat Endpoint
```
POST /api/{user_id}/chat
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "message": "Add a task to buy groceries",
  "conversation_id": null
}
```

### Conversation Management
```
GET /api/{user_id}/conversations
GET /api/{user_id}/conversations/{conversation_id}
DELETE /api/{user_id}/conversations/{conversation_id}
```

## Key Components

### MCP Tools Structure
```
backend/
├── app/
│   ├── mcp/
│   │   ├── server.py          # MCP server initialization
│   │   └── tools/
│   │       ├── add_task.py
│   │       ├── list_tasks.py
│   │       ├── complete_task.py
│   │       ├── delete_task.py
│   │       └── update_task.py
```

### Data Models
```
backend/
├── app/
│   ├── models/
│   │   ├── conversation.py    # Conversation entity
│   │   ├── message.py         # Message entity
│   │   └── tool_call.py       # Tool call entity (extends Phase 2)
```

## Development Workflow

### Adding New MCP Tools
1. Create new tool in `backend/app/mcp/tools/`
2. Register tool in `backend/app/mcp/server.py`
3. Update `contracts/mcp-tools.json` with schema
4. Add corresponding tests

### Modifying Chat Behavior
1. Update agent instructions in `backend/app/services/agent_service.py`
2. Adjust prompt templates as needed
3. Test with various natural language inputs

## Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

### Frontend Tests
```bash
# Run frontend tests
npm test
```

## Troubleshooting

### Common Issues

1. **Authentication failures**: Verify JWT token matches user_id in URL
2. **MCP tools not found**: Check that MCP server is running and tools are registered
3. **Database connection errors**: Verify DATABASE_URL and connection pooling settings
4. **Conversation persistence**: Check that conversation and message tables were created

### Debugging AI Responses
- Enable detailed logging in agent service
- Check tool call logs in database
- Verify conversation history reconstruction