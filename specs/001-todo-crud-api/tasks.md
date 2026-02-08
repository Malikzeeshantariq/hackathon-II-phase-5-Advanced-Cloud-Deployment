# Tasks: Todo CRUD API

**Feature**: 001-todo-crud-api
**Input**: Design documents from `/specs/001-todo-crud-api/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/openapi.yaml
**Updated**: 2026-01-10 (Spec Clarification Alignment)

## Purpose

Break down the approved plan into discrete, traceable tasks.
Each task represents a unit of work that can be implemented and verified.

**NO code may exist without a Task ID from this document.**

---

## Task Conventions

- Task IDs are immutable (T001, T002, ...)
- Tasks MUST reference `/sp.specify` requirements
- Tasks MUST be implemented exactly as described
- Partial completion is not allowed
- [P] = Parallelizable (different files, no dependencies)
- [US#] = User Story reference

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [X] T001 Create backend directory structure per plan.md: `backend/app/{models,routers,middleware,schemas}/`
- [X] T002 [P] Create frontend directory structure per plan.md: `frontend/{app,components,lib}/`
- [X] T003 [P] Create backend requirements.txt with FastAPI, SQLModel, python-jose, uvicorn dependencies
- [X] T004 [P] Create frontend package.json with Next.js, React, Better Auth, Axios, Tailwind dependencies
- [X] T005 [P] Create .env.example with BETTER_AUTH_SECRET, DATABASE_URL, CORS_ORIGINS, NEXT_PUBLIC_API_URL
- [X] T006 [P] Configure Tailwind CSS in frontend/tailwind.config.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create database connection module in backend/app/database.py (Neon PostgreSQL)
- [X] T008 Create environment config module in backend/app/config.py
- [X] T009 [P] Create Task SQLModel in backend/app/models/task.py per data-model.md (FR-001 to FR-011)
- [X] T010 [P] Create Pydantic schemas in backend/app/schemas/task.py (TaskCreate, TaskUpdate, TaskResponse)
- [X] T011 Create JWT verification middleware in backend/app/middleware/auth.py (AR-001, AR-002)
- [X] T012 Create FastAPI app entry point in backend/app/main.py with CORS and middleware
- [X] T013 [P] Create Better Auth client config in frontend/lib/auth.ts
- [X] T014 [P] Create API client with JWT headers in frontend/lib/api-client.ts
- [X] T015 [P] Create TypeScript types in frontend/lib/types.ts
- [X] T016 Create root layout with auth provider in frontend/app/layout.tsx
- [X] T017 [P] Create AuthGuard component in frontend/components/AuthGuard.tsx

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 & 2 - Create and View Tasks (Priority: P1)

**Goal**: Users can create tasks and view their task list

**Independent Test**: Create a task, verify it appears in the list with `completed = false`

**Spec References**: FR-001 to FR-006, US-1, US-2

### Implementation for User Story 1 & 2

- [X] T018 [US1] Implement POST `/api/{user_id}/tasks` endpoint in backend/app/routers/tasks.py (FR-001 to FR-004)
- [X] T019 [US2] Implement GET `/api/{user_id}/tasks` endpoint in backend/app/routers/tasks.py (FR-005, FR-006)
- [X] T020 [US2] Implement GET `/api/{user_id}/tasks/{id}` endpoint in backend/app/routers/tasks.py (FR-005)
- [X] T021 Register tasks router in backend/app/main.py
- [X] T022 [P] [US2] Create TaskList component in frontend/components/TaskList.tsx
- [X] T023 [P] [US1] Create TaskForm component in frontend/components/TaskForm.tsx
- [X] T024 [P] [US2] Create TaskItem component in frontend/components/TaskItem.tsx
- [X] T025 [US1] [US2] Create dashboard page in frontend/app/dashboard/page.tsx
- [X] T026 Create protected dashboard layout in frontend/app/dashboard/layout.tsx

**Checkpoint**: Users can create and view their tasks (MVP complete)

---

## Phase 4: User Story 3 & 4 - Update and Complete Tasks (Priority: P2)

**Goal**: Users can update task details and mark tasks as completed

**Independent Test**: Create a task, update its title, mark it complete, verify changes persist

**Spec References**: FR-007 to FR-009, US-3, US-4

### Implementation for User Story 3 & 4

- [X] T027 [US3] Implement PUT `/api/{user_id}/tasks/{id}` endpoint in backend/app/routers/tasks.py (FR-007, FR-008)
- [X] T028 [US4] Implement PATCH `/api/{user_id}/tasks/{id}/complete` endpoint in backend/app/routers/tasks.py (FR-009)
- [X] T029 [US3] Add edit mode to TaskItem component in frontend/components/TaskItem.tsx
- [X] T030 [US4] Add complete toggle to TaskItem component in frontend/components/TaskItem.tsx
- [X] T031 [US3] [US4] Update dashboard page to handle update and complete actions in frontend/app/dashboard/page.tsx

**Checkpoint**: Users can update and complete their tasks

---

## Phase 5: User Story 5 - Delete Tasks (Priority: P3)

**Goal**: Users can delete tasks they no longer need

**Independent Test**: Create a task, delete it, verify it no longer appears in the list

**Spec References**: FR-010, FR-011, US-5

### Implementation for User Story 5

- [X] T032 [US5] Implement DELETE `/api/{user_id}/tasks/{id}` endpoint in backend/app/routers/tasks.py (FR-010, FR-011)
- [X] T033 [US5] Add delete action to TaskItem component in frontend/components/TaskItem.tsx
- [X] T034 [US5] Update dashboard page to handle delete action in frontend/app/dashboard/page.tsx

**Checkpoint**: Full CRUD functionality complete

---

## Phase 6: Authentication UI

**Goal**: Users can sign up, log in, and access protected routes

**Spec References**: AR-001, Better Auth integration

### Implementation for Auth UI

- [X] T035 [P] Create login page in frontend/app/(auth)/login/page.tsx
- [X] T036 [P] Create signup page in frontend/app/(auth)/signup/page.tsx
- [X] T037 Create landing page in frontend/app/page.tsx with auth redirects

**Checkpoint**: Complete authentication flow

---

## Phase 7: Cross-Cutting Concerns

**Purpose**: Error handling, authorization enforcement, and polish

**Spec References**: AR-002 to AR-005, Error Handling Requirements

- [X] T038 Implement user ID validation (JWT user must match URL user_id) in backend/app/middleware/auth.py (AR-005)
- [X] T039 Implement 401 Unauthorized response for missing/invalid JWT in backend/app/middleware/auth.py (AR-002)
- [X] T040 Implement 403 Forbidden response for cross-user access in backend/app/routers/tasks.py (AR-003, AR-004)
- [X] T041 Implement 404 Not Found response for missing tasks in backend/app/routers/tasks.py
- [X] T042 Implement 422 Validation Error responses in backend/app/schemas/task.py
- [X] T043 [P] Add error handling and loading states to TaskList component in frontend/components/TaskList.tsx
- [X] T044 [P] Add error display to TaskForm component in frontend/components/TaskForm.tsx

**Checkpoint**: All error paths handled correctly

---

## Phase 8: Polish & Validation

**Purpose**: Final verification and cleanup

- [X] T045 Run quickstart.md validation (backend starts, frontend starts, end-to-end test)
- [X] T046 Verify user isolation (SC-005): Test that users cannot see each other's tasks
- [X] T047 Verify auth enforcement (SC-003, SC-004): Test 401/403 responses

---

## Phase 9: Spec Clarification Alignment (2026-01-10)

**Purpose**: Align implementation with clarified spec from `/sp.clarify` session

**Clarifications Applied**:
| Clarification | Decision | Task |
|--------------|----------|------|
| Task title max length | 255 characters | Already correct in T010 |
| Task ID format | UUID | Already correct in T009 |
| Task description max length | 2000 characters | T048 (was 10000) |
| Completion behavior | Toggle (complete/uncomplete) | Already correct in T028 |
| Update semantics | Partial updates (PATCH style) | Already correct in T027 |

### Implementation for Spec Alignment

- [X] T048 Fix description max_length from 10000 to 2000 in backend/app/schemas/task.py (Clarification: 2000 chars)
- [X] T049 [P] Add test for title exceeding 255 chars in backend/tests/test_tasks.py
- [X] T050 [P] Add test for description exceeding 2000 chars in backend/tests/test_tasks.py

**Checkpoint**: Implementation fully aligned with clarified spec

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ─────────────────────────────────────────┐
                                                         │
Phase 2 (Foundational) ──────────────────────────────────┤
         │                                               │
         ├─→ Phase 3 (US1 & US2 - Create/View) ──────────┤
         │                                               │
         ├─→ Phase 4 (US3 & US4 - Update/Complete) ──────┤
         │                                               │
         ├─→ Phase 5 (US5 - Delete) ─────────────────────┤
         │                                               │
         └─→ Phase 6 (Auth UI) ──────────────────────────┤
                                                         │
Phase 7 (Cross-Cutting) ─────────────────────────────────┤
                                                         │
Phase 8 (Polish) ────────────────────────────────────────┘
```

### User Story Dependencies

- **User Story 1 & 2 (P1)**: Depends on Phase 2 completion only - Can start immediately after foundation
- **User Story 3 & 4 (P2)**: Can run in parallel with US1/US2 after foundation
- **User Story 5 (P3)**: Can run in parallel with other stories after foundation

### Within Each Phase

- Models before services
- Backend before frontend integration
- Core implementation before error handling

### Parallel Opportunities

Tasks marked [P] can run in parallel within their phase:
- T002, T003, T004, T005, T006 (Phase 1)
- T009, T010, T013, T014, T015, T017 (Phase 2)
- T022, T023, T024 (Phase 3)
- T035, T036 (Phase 6)
- T043, T044 (Phase 7)

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Stories 1 & 2 (Create + View)
4. **STOP and VALIDATE**: Test task creation and viewing
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 & US2 → Test → Deploy (MVP!)
3. Add US3 & US4 → Test → Deploy (Update/Complete)
4. Add US5 → Test → Deploy (Delete)
5. Add Auth UI → Test → Deploy (Full auth flow)
6. Cross-cutting + Polish → Final release

---

## Agent Delegation

Per CLAUDE.md, delegate tasks to specialized agents:

| Task Range | Agent | Responsibility |
|------------|-------|----------------|
| T007-T012, T018-T021, T027-T028, T032, T038-T042 | backend-engineer | FastAPI routes, middleware |
| T009-T010 | database-architect | SQLModel schemas |
| T013-T017, T022-T026, T029-T031, T033-T037, T043-T044 | frontend-engineer | Next.js components |
| T011, T013, T038-T039 | hackathon-todo-auth | JWT/Better Auth |

---

## Completion Criteria

Phase 2 is complete when:

- [X] All tasks T001 through T050 are implemented
- [X] Each code artifact references its Task ID
- [X] No behavior exists outside this task list
- [X] Application runs end-to-end successfully
- [X] User isolation verified (SC-005)
- [X] Auth enforcement verified (SC-003, SC-004)
- [X] Spec clarifications from /sp.clarify aligned (T048-T050)

---

## Enforcement

If a required behavior is missing:
- A new task MUST be added
- Existing tasks MUST NOT be modified silently

If ambiguity is found:
- Stop implementation
- Update specs before continuing

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [US#] label maps task to specific user story for traceability
- Each user story phase is independently completable and testable
- Verify tests pass before moving to next phase
- Commit after each task or logical group
