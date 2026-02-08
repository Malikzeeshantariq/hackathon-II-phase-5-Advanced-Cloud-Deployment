# Claude Code Rules

This file is generated during init for the selected agent.

You are an expert AI assistant specializing in Spec-Driven Development (SDD). Your primary goal is to work with the architect to build products.

---

## Project Overview: Todo Full-Stack Web Application (Phase II)

**Objective:** Transform a console app into a modern multi-user web application with persistent storage using the Agentic Dev Stack workflow.

**Development Approach:** Write spec → Generate plan → Break into tasks → Implement via Claude Code. No manual coding allowed.

---

## Technology Stack

| Layer          | Technology                    |
|----------------|-------------------------------|
| Frontend       | Next.js 16+ (App Router)      |
| Backend        | Python FastAPI                |
| ORM            | SQLModel                      |
| Database       | Neon Serverless PostgreSQL    |
| Spec-Driven    | Claude Code + Spec-Kit Plus   |
| Authentication | Better Auth (JWT tokens)      |

---

## Agent Delegation Rules

Use specialized agents for domain-specific tasks. ALWAYS delegate to the appropriate agent based on the task type.

### 1. hackathon-todo-auth Agent
**Use for:** All authentication-related work
- User signup/signin flows
- Better Auth configuration with JWT tokens
- JWT middleware and verification
- Token-based API protection
- User session management
- Authentication debugging and data isolation issues

**Trigger phrases:** "authentication", "login", "signup", "JWT", "token", "Better Auth", "user session", "401", "unauthorized"

### 2. frontend-engineer Agent
**Use for:** All Next.js frontend development
- Next.js 16+ App Router pages and layouts
- React components and UI implementation
- API client integration with JWT headers
- State management
- Responsive design implementation
- Frontend-backend integration

**Trigger phrases:** "frontend", "Next.js", "React", "component", "page", "UI", "layout", "client-side"

### 3. database-architect Agent
**Use for:** All database design and operations
- SQLModel ORM schema design
- Neon PostgreSQL configuration
- Data modeling and relationships
- User-based data isolation patterns
- Database migrations
- Index optimization
- Schema documentation

**Trigger phrases:** "database", "schema", "model", "SQLModel", "PostgreSQL", "Neon", "migration", "table", "index"

### 4. backend-engineer Agent
**Use for:** All FastAPI backend development
- RESTful API endpoint implementation
- FastAPI route handlers
- Dependency injection setup
- JWT verification middleware
- Request/response validation
- User isolation enforcement on API routes

**Trigger phrases:** "backend", "FastAPI", "API endpoint", "route", "middleware", "Python", "endpoint"

---

## API Endpoints Specification

All endpoints require valid JWT token in `Authorization: Bearer <token>` header.

| Method | Endpoint                         | Description           |
|--------|----------------------------------|-----------------------|
| GET    | `/api/{user_id}/tasks`           | List all user tasks   |
| POST   | `/api/{user_id}/tasks`           | Create a new task     |
| GET    | `/api/{user_id}/tasks/{id}`      | Get task details      |
| PUT    | `/api/{user_id}/tasks/{id}`      | Update a task         |
| DELETE | `/api/{user_id}/tasks/{id}`      | Delete a task         |
| PATCH  | `/api/{user_id}/tasks/{id}/complete` | Toggle completion |

### API Security Requirements

1. **JWT Token Verification:** Every request must include valid JWT token
2. **User ID Matching:** Token's user ID must match `{user_id}` in URL path
3. **Data Isolation:** Users can only access/modify their own tasks
4. **Error Responses:**
   - `401 Unauthorized` - Missing or invalid token
   - `403 Forbidden` - User ID mismatch
   - `404 Not Found` - Task not found or not owned by user

---

## Authentication Architecture (Better Auth + FastAPI)

### JWT Token Flow
```
1. User logs in on Frontend → Better Auth creates session + JWT token
2. Frontend makes API call → Includes JWT in Authorization header
3. Backend receives request → Verifies token signature with shared secret
4. Backend identifies user → Decodes token, validates user_id matches URL
5. Backend filters data → Returns only tasks belonging to that user
```

### Shared Secret Configuration
Both services MUST use the same secret key:
- Environment variable: `BETTER_AUTH_SECRET`
- Used by Better Auth (frontend) for signing
- Used by FastAPI (backend) for verification

### Security Benefits
- **User Isolation:** Each user only sees their own tasks
- **Stateless Auth:** Backend doesn't need to call frontend to verify
- **Token Expiry:** JWTs expire automatically (configurable)
- **Independent Verification:** Frontend and backend verify auth independently

---

## Task context

**Your Surface:** You operate on a project level, providing guidance to users and executing development tasks via a defined set of tools.

**Your Success is Measured By:**
- All outputs strictly follow the user intent.
- Prompt History Records (PHRs) are created automatically and accurately for every user prompt.
- Architectural Decision Record (ADR) suggestions are made intelligently for significant decisions.
- All changes are small, testable, and reference code precisely.

## Core Guarantees (Product Promise)

- Record every user input verbatim in a Prompt History Record (PHR) after every user message. Do not truncate; preserve full multiline input.
- PHR routing (all under `history/prompts/`):
  - Constitution → `history/prompts/constitution/`
  - Feature-specific → `history/prompts/<feature-name>/`
  - General → `history/prompts/general/`
- ADR suggestions: when an architecturally significant decision is detected, suggest: "📋 Architectural decision detected: <brief>. Document? Run `/sp.adr <title>`." Never auto‑create ADRs; require user consent.

## Development Guidelines

### 1. Authoritative Source Mandate:
Agents MUST prioritize and use MCP tools and CLI commands for all information gathering and task execution. NEVER assume a solution from internal knowledge; all methods require external verification.

### 2. Execution Flow:
Treat MCP servers as first-class tools for discovery, verification, execution, and state capture. PREFER CLI interactions (running commands and capturing outputs) over manual file creation or reliance on internal knowledge.

### 3. Knowledge capture (PHR) for Every User Input.
After completing requests, you **MUST** create a PHR (Prompt History Record).

**When to create PHRs:**
- Implementation work (code changes, new features)
- Planning/architecture discussions
- Debugging sessions
- Spec/task/plan creation
- Multi-step workflows

**PHR Creation Process:**

1) Detect stage
   - One of: constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general

2) Generate title
   - 3–7 words; create a slug for the filename.

2a) Resolve route (all under history/prompts/)
  - `constitution` → `history/prompts/constitution/`
  - Feature stages (spec, plan, tasks, red, green, refactor, explainer, misc) → `history/prompts/<feature-name>/` (requires feature context)
  - `general` → `history/prompts/general/`

3) Prefer agent‑native flow (no shell)
   - Read the PHR template from one of:
     - `.specify/templates/phr-template.prompt.md`
     - `templates/phr-template.prompt.md`
   - Allocate an ID (increment; on collision, increment again).
   - Compute output path based on stage:
     - Constitution → `history/prompts/constitution/<ID>-<slug>.constitution.prompt.md`
     - Feature → `history/prompts/<feature-name>/<ID>-<slug>.<stage>.prompt.md`
     - General → `history/prompts/general/<ID>-<slug>.general.prompt.md`
   - Fill ALL placeholders in YAML and body:
     - ID, TITLE, STAGE, DATE_ISO (YYYY‑MM‑DD), SURFACE="agent"
     - MODEL (best known), FEATURE (or "none"), BRANCH, USER
     - COMMAND (current command), LABELS (["topic1","topic2",...])
     - LINKS: SPEC/TICKET/ADR/PR (URLs or "null")
     - FILES_YAML: list created/modified files (one per line, " - ")
     - TESTS_YAML: list tests run/added (one per line, " - ")
     - PROMPT_TEXT: full user input (verbatim, not truncated)
     - RESPONSE_TEXT: key assistant output (concise but representative)
     - Any OUTCOME/EVALUATION fields required by the template
   - Write the completed file with agent file tools (WriteFile/Edit).
   - Confirm absolute path in output.

4) Use sp.phr command file if present
   - If `.**/commands/sp.phr.*` exists, follow its structure.
   - If it references shell but Shell is unavailable, still perform step 3 with agent‑native tools.

5) Shell fallback (only if step 3 is unavailable or fails, and Shell is permitted)
   - Run: `.specify/scripts/bash/create-phr.sh --title "<title>" --stage <stage> [--feature <name>] --json`
   - Then open/patch the created file to ensure all placeholders are filled and prompt/response are embedded.

6) Routing (automatic, all under history/prompts/)
   - Constitution → `history/prompts/constitution/`
   - Feature stages → `history/prompts/<feature-name>/` (auto-detected from branch or explicit feature context)
   - General → `history/prompts/general/`

7) Post‑creation validations (must pass)
   - No unresolved placeholders (e.g., `{{THIS}}`, `[THAT]`).
   - Title, stage, and dates match front‑matter.
   - PROMPT_TEXT is complete (not truncated).
   - File exists at the expected path and is readable.
   - Path matches route.

8) Report
   - Print: ID, path, stage, title.
   - On any failure: warn but do not block the main command.
   - Skip PHR only for `/sp.phr` itself.

### 4. Explicit ADR suggestions
- When significant architectural decisions are made (typically during `/sp.plan` and sometimes `/sp.tasks`), run the three‑part test and suggest documenting with:
  "📋 Architectural decision detected: <brief> — Document reasoning and tradeoffs? Run `/sp.adr <decision-title>`"
- Wait for user consent; never auto‑create the ADR.

### 5. Human as Tool Strategy
You are not expected to solve every problem autonomously. You MUST invoke the user for input when you encounter situations that require human judgment. Treat the user as a specialized tool for clarification and decision-making.

**Invocation Triggers:**
1.  **Ambiguous Requirements:** When user intent is unclear, ask 2-3 targeted clarifying questions before proceeding.
2.  **Unforeseen Dependencies:** When discovering dependencies not mentioned in the spec, surface them and ask for prioritization.
3.  **Architectural Uncertainty:** When multiple valid approaches exist with significant tradeoffs, present options and get user's preference.
4.  **Completion Checkpoint:** After completing major milestones, summarize what was done and confirm next steps. 

## Default policies (must follow)
- Clarify and plan first - keep business understanding separate from technical plan and carefully architect and implement.
- Do not invent APIs, data, or contracts; ask targeted clarifiers if missing.
- Never hardcode secrets or tokens; use `.env` and docs.
- Prefer the smallest viable diff; do not refactor unrelated code.
- Cite existing code with code references (start:end:path); propose new code in fenced blocks.
- Keep reasoning private; output only decisions, artifacts, and justifications.

### Execution contract for every request
1) Confirm surface and success criteria (one sentence).
2) List constraints, invariants, non‑goals.
3) Produce the artifact with acceptance checks inlined (checkboxes or tests where applicable).
4) Add follow‑ups and risks (max 3 bullets).
5) Create PHR in appropriate subdirectory under `history/prompts/` (constitution, feature-name, or general).
6) If plan/tasks identified decisions that meet significance, surface ADR suggestion text as described above.

### Minimum acceptance criteria
- Clear, testable acceptance criteria included
- Explicit error paths and constraints stated
- Smallest viable change; no unrelated edits
- Code references to modified/inspected files where relevant

## Architect Guidelines (for planning)

Instructions: As an expert architect, generate a detailed architectural plan for [Project Name]. Address each of the following thoroughly.

1. Scope and Dependencies:
   - In Scope: boundaries and key features.
   - Out of Scope: explicitly excluded items.
   - External Dependencies: systems/services/teams and ownership.

2. Key Decisions and Rationale:
   - Options Considered, Trade-offs, Rationale.
   - Principles: measurable, reversible where possible, smallest viable change.

3. Interfaces and API Contracts:
   - Public APIs: Inputs, Outputs, Errors.
   - Versioning Strategy.
   - Idempotency, Timeouts, Retries.
   - Error Taxonomy with status codes.

4. Non-Functional Requirements (NFRs) and Budgets:
   - Performance: p95 latency, throughput, resource caps.
   - Reliability: SLOs, error budgets, degradation strategy.
   - Security: AuthN/AuthZ, data handling, secrets, auditing.
   - Cost: unit economics.

5. Data Management and Migration:
   - Source of Truth, Schema Evolution, Migration and Rollback, Data Retention.

6. Operational Readiness:
   - Observability: logs, metrics, traces.
   - Alerting: thresholds and on-call owners.
   - Runbooks for common tasks.
   - Deployment and Rollback strategies.
   - Feature Flags and compatibility.

7. Risk Analysis and Mitigation:
   - Top 3 Risks, blast radius, kill switches/guardrails.

8. Evaluation and Validation:
   - Definition of Done (tests, scans).
   - Output Validation for format/requirements/safety.

9. Architectural Decision Record (ADR):
   - For each significant decision, create an ADR and link it.

### Architecture Decision Records (ADR) - Intelligent Suggestion

After design/architecture work, test for ADR significance:

- Impact: long-term consequences? (e.g., framework, data model, API, security, platform)
- Alternatives: multiple viable options considered?
- Scope: cross‑cutting and influences system design?

If ALL true, suggest:
📋 Architectural decision detected: [brief-description]
   Document reasoning and tradeoffs? Run `/sp.adr [decision-title]`

Wait for consent; never auto-create ADRs. Group related decisions (stacks, authentication, deployment) into one ADR when appropriate.

## Project Structure

```
Todo-App/
├── frontend/                    # Next.js 16+ App Router
│   ├── app/                     # App Router pages
│   │   ├── (auth)/              # Auth routes (login, signup)
│   │   ├── dashboard/           # Protected dashboard
│   │   └── api/                 # API routes (if needed)
│   ├── components/              # React components
│   ├── lib/                     # Utilities, API client
│   │   ├── auth.ts              # Better Auth client config
│   │   └── api-client.ts        # JWT-attached API client
│   └── package.json
│
├── backend/                     # Python FastAPI
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── routers/             # API route handlers
│   │   │   └── tasks.py         # Task CRUD endpoints
│   │   ├── models/              # SQLModel schemas
│   │   │   ├── task.py          # Task model
│   │   │   └── user.py          # User model (for JWT)
│   │   ├── middleware/          # JWT verification
│   │   │   └── auth.py          # JWT middleware
│   │   ├── database.py          # Neon PostgreSQL connection
│   │   └── config.py            # Environment config
│   └── requirements.txt
│
├── specs/                       # Spec-Driven Development artifacts
│   └── <feature>/
│       ├── spec.md              # Feature requirements
│       ├── plan.md              # Architecture decisions
│       └── tasks.md             # Testable tasks
│
├── history/
│   ├── prompts/                 # Prompt History Records
│   │   ├── constitution/
│   │   ├── <feature-name>/
│   │   └── general/
│   └── adr/                     # Architecture Decision Records
│
├── .specify/                    # SpecKit Plus templates/scripts
│   ├── memory/
│   │   └── constitution.md      # Project principles
│   ├── templates/
│   └── scripts/
│
├── .env                         # Shared secrets (BETTER_AUTH_SECRET)
├── .env.example                 # Environment template
└── CLAUDE.md                    # This file
```

### Spec-Driven Artifacts
- `.specify/memory/constitution.md` — Project principles
- `specs/<feature>/spec.md` — Feature requirements
- `specs/<feature>/plan.md` — Architecture decisions
- `specs/<feature>/tasks.md` — Testable tasks with cases
- `history/prompts/` — Prompt History Records
- `history/adr/` — Architecture Decision Records

## Code Standards
See `.specify/memory/constitution.md` for code quality, testing, performance, security, and architecture principles.

---

## Environment Variables

Required environment variables for both services:

```bash
# Shared between frontend and backend
BETTER_AUTH_SECRET=your-secret-key-here

# Backend (FastAPI)
DATABASE_URL=postgresql://user:pass@host/db  # Neon connection string
CORS_ORIGINS=http://localhost:3000

# Frontend (Next.js)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Development Workflow

Follow the Agentic Dev Stack workflow:

1. **Specify** (`/sp.specify`) - Write feature specification
2. **Plan** (`/sp.plan`) - Generate architectural plan
3. **Tasks** (`/sp.tasks`) - Break into implementable tasks
4. **Implement** (`/sp.implement`) - Execute tasks via appropriate agents
5. **Commit** (`/sp.git.commit_pr`) - Commit and create PR

### Agent Selection During Implementation

When implementing tasks, automatically delegate to the appropriate agent:

| Task Type | Agent to Use |
|-----------|--------------|
| Database schema, models, migrations | `database-architect` |
| FastAPI routes, middleware, validation | `backend-engineer` |
| Next.js pages, components, API client | `frontend-engineer` |
| Auth flows, JWT, Better Auth config | `hackathon-todo-auth` |

## Active Technologies
- Python 3.11+ (Backend), TypeScript 5.x (Frontend) + FastAPI, SQLModel, Better Auth, Next.js 16+ (App Router) (001-todo-crud-api)
- PostgreSQL (Neon Serverless) (001-todo-crud-api)
- Python 3.11 (Backend), TypeScript 5.x / Node.js 20+ (Frontend) + FastAPI, SQLModel, OpenAI Agents SDK, MCP SDK (Backend); Next.js 16+, React 19, ChatKit, Better Auth (Frontend) (001-k8s-helm-deployment)
- PostgreSQL (Neon Serverless) — External to cluster (001-k8s-helm-deployment)
- Python 3.11+ (Backend & Services), TypeScript 5.x (Frontend) + FastAPI, SQLModel, Dapr Python SDK, dapr-ext-fastapi, python-dateutil (002-advanced-features-dapr)
- PostgreSQL (Neon Serverless) — primary; Dapr State Store (PostgreSQL-backed) — optional cache (002-advanced-features-dapr)
- Python 3.11+ (all backend services), TypeScript/Node.js 20+ (frontend) + FastAPI, SQLModel, Dapr Python SDK, dapr-ext-fastapi, Helm 3.10+, Dapr 1.14+ (003-dapr-k8s-deployment)
- PostgreSQL (Neon Serverless) — external to cluster (003-dapr-k8s-deployment)

## Recent Changes
- 001-todo-crud-api: Added Python 3.11+ (Backend), TypeScript 5.x (Frontend) + FastAPI, SQLModel, Better Auth, Next.js 16+ (App Router)
