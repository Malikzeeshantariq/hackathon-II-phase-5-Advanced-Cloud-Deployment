# Implementation Plan: Todo CRUD API

**Branch**: `001-todo-crud-api` | **Date**: 2025-01-08 | **Updated**: 2026-01-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-todo-crud-api/spec.md`

## Summary

Implement a JWT-protected RESTful API for task management with full CRUD operations. The system will use FastAPI backend with SQLModel ORM connecting to Neon PostgreSQL, and a Next.js frontend with Better Auth handling authentication. All operations enforce user isolation - users can only access their own tasks.

**Implementation Status**: Complete. All endpoints, authentication, and UI are implemented and aligned with spec clarifications.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.x (Frontend)
**Primary Dependencies**: FastAPI, SQLModel, Better Auth, Next.js 16+ (App Router)
**Storage**: PostgreSQL (Neon Serverless)
**Testing**: pytest (backend), Jest/Vitest (frontend)
**Target Platform**: Web (Linux server for backend, Vercel/Node for frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: CRUD operations complete within 2 seconds (SC-001)
**Constraints**: Stateless backend, JWT verification on every request
**Scale/Scope**: Multi-user application with user-isolated data access

## Spec Clarifications (2026-01-10)

The following clarifications were made via `/sp.clarify` and are reflected in the implementation:

| Clarification | Decision | Impact |
|--------------|----------|--------|
| Task title max length | 255 characters | Pydantic schema validation |
| Task ID format | UUID | SQLModel primary key type |
| Task description max length | 2000 characters | Pydantic schema validation |
| Completion behavior | Toggle (can complete/uncomplete) | PATCH endpoint toggles status |
| Update semantics | Partial updates (PATCH style) | TaskUpdate has optional fields |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Accuracy Through Specifications | PASS | All features traceable to spec FR-001 through FR-011 |
| II. Clarity for Technical Audience | PASS | Clear naming conventions, explicit API contracts |
| III. Reproducibility | PASS | Environment config via .env, documented dependencies |
| IV. Engineering Rigor | PASS | Stable REST API contracts, clear separation of concerns |

**Architecture Constraints Check**:

| Constraint | Status | Implementation |
|------------|--------|----------------|
| Monorepo structure | PASS | `/frontend` and `/backend` directories |
| RESTful APIs only | PASS | Standard REST endpoints defined |
| User-scoped data access | PASS | JWT-based user isolation enforced |
| No server-side sessions | PASS | Stateless JWT authentication |

**Security Check**:

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Protected routes require JWT | PASS | FastAPI dependency injection middleware |
| Cross-user access returns 403 | PASS | User ID validation in all endpoints |
| Unauthorized returns 401 | PASS | JWT verification middleware |
| No secrets in repository | PASS | Environment variables for BETTER_AUTH_SECRET |

## Project Structure

### Documentation (this feature)

```text
specs/001-todo-crud-api/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Technology decisions
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Development setup guide
├── contracts/           # Phase 1: API contracts
│   └── openapi.yaml     # OpenAPI 3.0 specification
└── tasks.md             # Phase 2: Implementation tasks (created by /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # Neon PostgreSQL connection
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py          # Task SQLModel
│   ├── routers/
│   │   ├── __init__.py
│   │   └── tasks.py         # Task CRUD endpoints
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py          # JWT verification middleware
│   └── schemas/
│       ├── __init__.py
│       └── task.py          # Pydantic request/response schemas
├── tests/
│   ├── conftest.py
│   ├── test_tasks.py        # Task endpoint tests
│   └── test_auth.py         # Auth middleware tests
└── requirements.txt

frontend/
├── app/
│   ├── layout.tsx           # Root layout with auth provider
│   ├── page.tsx             # Landing/home page
│   ├── (auth)/
│   │   ├── login/page.tsx   # Login page
│   │   └── signup/page.tsx  # Signup page
│   └── dashboard/
│       ├── page.tsx         # Task list view
│       └── layout.tsx       # Protected layout
├── components/
│   ├── TaskList.tsx         # Task list component
│   ├── TaskItem.tsx         # Individual task component
│   ├── TaskForm.tsx         # Create/edit task form
│   └── AuthGuard.tsx        # Route protection component
├── lib/
│   ├── auth.ts              # Better Auth client configuration
│   ├── api-client.ts        # JWT-attached API client
│   └── types.ts             # TypeScript type definitions
├── package.json
└── tailwind.config.ts
```

**Structure Decision**: Web application structure selected per constitution's monorepo constraint. Frontend and backend are separate directories with clear boundaries. This enables independent deployment and testing while maintaining a single repository.

## Complexity Tracking

> No violations - plan adheres to constitution constraints.

| Aspect | Complexity Level | Justification |
|--------|------------------|---------------|
| API Design | Low | Standard REST CRUD operations |
| Authentication | Medium | JWT verification, shared secret between services |
| Data Model | Low | Single Task entity with user ownership |
| Frontend | Low | Basic CRUD UI with task list |

## Component Responsibilities

### Backend Components

| Component | Responsibility | Spec Reference |
|-----------|----------------|----------------|
| `main.py` | FastAPI app initialization, CORS, middleware | - |
| `database.py` | Neon PostgreSQL connection, session management | - |
| `models/task.py` | Task SQLModel definition | FR-001 to FR-011 |
| `routers/tasks.py` | CRUD endpoint handlers | All user stories |
| `middleware/auth.py` | JWT verification, user extraction | AR-001 to AR-005 |
| `schemas/task.py` | Request/response validation | Error handling |

### Frontend Components

| Component | Responsibility | Spec Reference |
|-----------|----------------|----------------|
| `auth.ts` | Better Auth configuration, JWT handling | AR-001 |
| `api-client.ts` | Axios instance with JWT headers | AR-001 |
| `TaskList.tsx` | Display user's tasks | US-2 (View Tasks) |
| `TaskItem.tsx` | Individual task with actions | US-3, US-4, US-5 |
| `TaskForm.tsx` | Create/edit task form | US-1, US-3 |

## Request Flow

```
User Action → Frontend Component → API Client (+ JWT) → FastAPI Router
    → JWT Middleware (verify + extract user_id)
    → Route Handler (validate user ownership)
    → SQLModel Query (user-scoped)
    → Response → Frontend → UI Update
```

## Security Implementation

### JWT Flow

1. **Login**: User authenticates via Better Auth → JWT token issued
2. **Storage**: Token stored in httpOnly cookie or memory
3. **API Call**: Frontend attaches token in `Authorization: Bearer <token>` header
4. **Verification**: Backend middleware decodes and validates JWT
5. **User Extraction**: `user_id` extracted from token payload
6. **Authorization**: Every query filters by `user_id` from token

### Shared Secret

```
BETTER_AUTH_SECRET environment variable
├── Frontend (Better Auth) → Signs JWT tokens
└── Backend (FastAPI) → Verifies JWT signatures
```

## API Endpoints Overview

| Method | Endpoint | Handler | Spec Reference |
|--------|----------|---------|----------------|
| GET | `/api/{user_id}/tasks` | `list_tasks()` | FR-005, FR-006 |
| POST | `/api/{user_id}/tasks` | `create_task()` | FR-001 to FR-004 |
| GET | `/api/{user_id}/tasks/{id}` | `get_task()` | FR-005 |
| PUT | `/api/{user_id}/tasks/{id}` | `update_task()` | FR-007, FR-008 |
| DELETE | `/api/{user_id}/tasks/{id}` | `delete_task()` | FR-010, FR-011 |
| PATCH | `/api/{user_id}/tasks/{id}/complete` | `complete_task()` | FR-009 |

## Error Response Mapping

| Condition | HTTP Status | Response Body |
|-----------|-------------|---------------|
| No/invalid JWT | 401 | `{"detail": "Not authenticated"}` |
| User ID mismatch | 403 | `{"detail": "Forbidden"}` |
| Task not found | 404 | `{"detail": "Task not found"}` |
| Validation error | 422 | `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` |

## Dependencies

### Backend (requirements.txt)

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlmodel>=0.0.14
psycopg2-binary>=2.9.9
python-jose[cryptography]>=3.3.0
python-dotenv>=1.0.0
pytest>=8.0.0
httpx>=0.26.0
```

### Frontend (package.json)

```json
{
  "dependencies": {
    "next": "^16.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "better-auth": "^1.0.0",
    "axios": "^1.6.0",
    "tailwindcss": "^3.4.0"
  }
}
```

## Environment Variables

```bash
# Shared
BETTER_AUTH_SECRET=<32+ character secret>

# Backend
DATABASE_URL=postgresql://user:pass@host/dbname
CORS_ORIGINS=http://localhost:3000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Implementation Status

All implementation phases are complete:

| Phase | Status | Notes |
|-------|--------|-------|
| Backend Foundation | Complete | FastAPI, SQLModel, Neon PostgreSQL |
| CRUD Endpoints | Complete | All 6 endpoints implemented |
| JWT Authentication | Complete | Middleware with user isolation |
| Frontend Integration | Complete | Next.js, Better Auth, all components |
| Spec Alignment | Complete | Description max_length fixed (2000 chars) |

## Next Steps

1. Configure environment variables (`.env` files)
2. Set up Neon PostgreSQL database
3. Run tests: `cd backend && pytest tests/ -v`
4. Verify end-to-end flow
5. Consider Phase 3 features (AI integration) after Phase 2 validation
