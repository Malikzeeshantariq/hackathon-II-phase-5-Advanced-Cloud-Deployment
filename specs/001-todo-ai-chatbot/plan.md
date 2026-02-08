# Implementation Plan: Todo AI Chatbot (Phase 3)

**Branch**: `001-todo-ai-chatbot` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-todo-ai-chatbot/spec.md`
**Governed By**: Phase 3 Constitution v2.0.0

## Summary

Implementation of an AI-powered conversational interface for the Todo application allowing authenticated users to manage tasks using natural language. The system uses OpenAI Agents SDK for intent recognition and Model Context Protocol (MCP) tools for deterministic task operations, with conversation persistence in PostgreSQL to maintain stateless server architecture.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.x (Frontend)
**Primary Dependencies**: FastAPI, SQLModel, OpenAI Agents SDK, MCP SDK, ChatKit
**Storage**: PostgreSQL (Neon Serverless) - conversations, messages, tool calls
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Linux server (containerized), Web browser (ChatKit UI)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: <10s task creation, <5s task listing, 95% intent accuracy
**Constraints**: Stateless servers, JWT auth required, tool-only AI execution
**Scale/Scope**: Single-tenant conversations, English language only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Specification-First | All AI behavior defined in spec | ✅ PASS |
| II. Deterministic AI via Tools | AI uses MCP tools exclusively | ✅ PASS |
| III. Stateless + Persistent Memory | Servers stateless, DB persistence | ✅ PASS |
| IV. Engineering Rigor | Typed schemas, explicit behavior | ✅ PASS |

### AI & MCP Governance Compliance

| Rule | Implementation | Status |
|------|---------------|--------|
| AI uses MCP tools only | 5 tools defined: add_task, list_tasks, complete_task, delete_task, update_task | ✅ |
| Tools are deterministic | Each tool performs exactly one DB operation | ✅ |
| Tools validate inputs | user_id, task_id required; ownership enforced | ✅ |
| AI asks for clarification | Spec FR-009, FR-010 mandate this | ✅ |
| Tool calls logged | Tool Call entity captures all invocations | ✅ |

**Constitution Gate**: PASSED

## Project Structure

### Documentation (this feature)

```text
specs/001-todo-ai-chatbot/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── chat-api.yaml    # Chat endpoint OpenAPI
│   └── mcp-tools.json   # MCP tool schemas
└── tasks.md             # Phase 2 output (/sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Environment config
│   ├── database.py          # Neon PostgreSQL connection
│   ├── routers/
│   │   ├── tasks.py         # Phase 2 task CRUD (existing)
│   │   └── chat.py          # Phase 3 chat endpoint
│   ├── models/
│   │   ├── task.py          # Phase 2 task model (existing)
│   │   ├── conversation.py  # New: conversation model
│   │   ├── message.py       # New: message model
│   │   └── tool_call.py     # New: tool call model
│   ├── services/
│   │   ├── chat_service.py  # Chat orchestration
│   │   └── agent_service.py # OpenAI Agents SDK wrapper
│   ├── mcp/
│   │   ├── server.py        # MCP server setup
│   │   └── tools/
│   │       ├── add_task.py
│   │       ├── list_tasks.py
│   │       ├── complete_task.py
│   │       ├── delete_task.py
│   │       └── update_task.py
│   └── middleware/
│       └── auth.py          # JWT verification (existing)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt

frontend/
├── app/
│   ├── (auth)/              # Auth routes (existing)
│   ├── dashboard/           # Dashboard (existing)
│   └── chat/                # New: ChatKit integration
│       └── page.tsx
├── components/
│   └── ChatPanel.tsx        # ChatKit wrapper component
├── lib/
│   ├── auth.ts              # Better Auth client (existing)
│   └── chat-client.ts       # Chat API client
└── package.json
```

**Structure Decision**: Web application structure with backend/ and frontend/ separation. Phase 3 adds chat endpoint, conversation models, MCP tools layer, and ChatKit frontend integration.

## Complexity Tracking

No constitution violations. Architecture follows all constraints:

| Constraint | Compliance |
|------------|------------|
| Single chat endpoint | ✅ POST /api/{user_id}/chat |
| MCP tools only | ✅ 5 tools, no direct DB in AI |
| Stateless servers | ✅ Context reconstructed per request |
| Conversation persistence | ✅ PostgreSQL storage |
| Tool call logging | ✅ tool_calls table |

## Re-evaluation After Design

### Architecture Compliance Check

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Specification-First | ✅ | All AI behavior defined in spec.md |
| Deterministic AI | ✅ | AI uses only MCP tools (no direct DB access) |
| Stateless Architecture | ✅ | Context reconstructed from DB per request |
| Tool Validation | ✅ | All tools validate user_id ownership |
| Audit Trail | ✅ | Tool calls logged with parameters/results |
| User Isolation | ✅ | All queries filtered by user_id from JWT |
| Horizontal Scaling | ✅ | No server state, DB persistence only |

**Post-Design Constitution Gate**: PASSED
