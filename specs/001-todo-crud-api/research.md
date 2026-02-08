# Research: Todo CRUD API

**Feature**: 001-todo-crud-api
**Date**: 2025-01-08
**Phase**: 0 - Research

## Purpose

Document technology decisions, alternatives considered, and rationale for the Todo CRUD API implementation.

---

## Technology Decisions

### 1. Backend Framework: FastAPI

**Decision**: Use FastAPI as the Python web framework.

**Rationale**:
- Constitution mandates FastAPI (Technical Constraints)
- Native async support for non-blocking operations (SC-006)
- Automatic OpenAPI documentation generation
- Pydantic integration for request/response validation
- Dependency injection system ideal for JWT middleware

**Alternatives Considered**:
- Flask: Simpler but lacks async support and automatic validation
- Django REST Framework: Too heavyweight for simple CRUD API

---

### 2. ORM: SQLModel

**Decision**: Use SQLModel for database operations.

**Rationale**:
- Constitution mandates SQLModel (Technical Constraints)
- Combines SQLAlchemy and Pydantic in single model definition
- Type-safe queries with IDE support
- Seamless integration with FastAPI

**Alternatives Considered**:
- SQLAlchemy alone: Would require separate Pydantic schemas
- Tortoise ORM: Less mature, smaller community

---

### 3. Database: Neon PostgreSQL

**Decision**: Use Neon Serverless PostgreSQL.

**Rationale**:
- Constitution mandates Neon PostgreSQL (Technical Constraints)
- Serverless scaling matches variable workload patterns
- PostgreSQL compatibility ensures standard SQL support
- Built-in connection pooling

**Alternatives Considered**:
- Supabase: Similar offering but Neon specified in constitution
- AWS RDS: Not serverless, higher operational overhead

---

### 4. Authentication: Better Auth with JWT

**Decision**: Use Better Auth for frontend authentication with JWT tokens for backend API security.

**Rationale**:
- Constitution mandates JWT-based authentication
- Better Auth provides modern auth primitives for Next.js
- JWT tokens enable stateless backend (constitution requirement)
- Shared secret allows independent verification

**Alternatives Considered**:
- NextAuth.js: More complex, session-based by default
- Auth0: External dependency, cost considerations
- Custom JWT: More work, Better Auth handles edge cases

---

### 5. Frontend Framework: Next.js 16+ (App Router)

**Decision**: Use Next.js with App Router.

**Rationale**:
- Constitution mandates Next.js App Router (Technical Constraints)
- Server components reduce client-side JavaScript
- Built-in routing and layouts
- Excellent TypeScript support

**Alternatives Considered**:
- React SPA: Would require additional routing setup
- Remix: Good alternative but Next.js specified

---

### 6. Styling: Tailwind CSS

**Decision**: Use Tailwind CSS for styling.

**Rationale**:
- Constitution mandates Tailwind CSS (Technical Constraints)
- Utility-first approach speeds development
- No CSS-in-JS runtime overhead
- Excellent responsive design primitives

**Alternatives Considered**:
- CSS Modules: More verbose, less consistent
- Styled Components: Runtime overhead

---

## JWT Implementation Details

### Token Structure

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "iat": 1704672000,
  "exp": 1705276800
}
```

### Verification Algorithm

- Algorithm: HS256 (HMAC with SHA-256)
- Secret: `BETTER_AUTH_SECRET` environment variable
- Expiry: 7 days (configurable)

### Backend Verification

```python
# Using python-jose library
from jose import jwt, JWTError

def verify_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.BETTER_AUTH_SECRET,
        algorithms=["HS256"]
    )
    return payload
```

---

## Database Schema Decisions

### Task Table Design

| Column | Type | Constraints | Rationale |
|--------|------|-------------|-----------|
| id | UUID | PRIMARY KEY | Globally unique, no sequential exposure |
| user_id | VARCHAR | NOT NULL, INDEX | User isolation, JWT-derived |
| title | VARCHAR(255) | NOT NULL | Required per FR-001 |
| description | TEXT | NULLABLE | Optional per FR-001 |
| completed | BOOLEAN | DEFAULT FALSE | FR-003 requirement |
| created_at | TIMESTAMP | DEFAULT NOW() | FR-004 requirement |
| updated_at | TIMESTAMP | ON UPDATE | FR-008 requirement |

### Index Strategy

- `idx_tasks_user_id`: All queries filter by user_id
- Primary key index on `id`: Single task lookups

---

## API Design Decisions

### URL Structure

**Decision**: Include `user_id` in URL path.

**Rationale**:
- Explicit user context in every request
- Enables backend to verify JWT user matches URL user
- Follows REST resource hierarchy: users have tasks

**Alternative Considered**:
- Derive user_id solely from JWT: Less explicit, harder to debug

### Response Format

**Decision**: Use JSON with consistent structure.

```json
{
  "id": "uuid",
  "title": "string",
  "description": "string | null",
  "completed": false,
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

---

## Error Handling Strategy

### HTTP Status Code Mapping

| Error Type | Status | Body |
|------------|--------|------|
| Missing/invalid JWT | 401 | `{"detail": "Not authenticated"}` |
| User ID mismatch | 403 | `{"detail": "Forbidden"}` |
| Task not found | 404 | `{"detail": "Task not found"}` |
| Validation error | 422 | FastAPI default validation response |

### Validation Rules

- Title: Required, 1-255 characters
- Description: Optional, max 10000 characters

---

## Outstanding Questions

None - all technology decisions are defined by constitution.

---

## References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLModel Documentation: https://sqlmodel.tiangolo.com/
- Better Auth Documentation: https://www.better-auth.com/
- Neon Documentation: https://neon.tech/docs/
- Next.js App Router: https://nextjs.org/docs/app
