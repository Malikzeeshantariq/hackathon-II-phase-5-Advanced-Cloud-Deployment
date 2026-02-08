# Feature Specification: Todo CRUD API

**Feature Branch**: `001-todo-crud-api`
**Created**: 2025-01-08
**Status**: Draft
**Input**: Todo App Phase 2 - CRUD operations with JWT authentication

## Purpose

Define the functional and behavioral requirements of the Todo Web Application.
This document specifies WHAT the system must do, independent of implementation.

This specification is authoritative for Phase 2.

---

## Clarifications

### Session 2026-01-10

- Q: What is the maximum allowed length for task titles? → A: 255 characters
- Q: What format should Task IDs use? → A: UUID
- Q: What is the maximum allowed length for task descriptions? → A: 2000 characters
- Q: Can a completed task be marked as incomplete (toggled back)? → A: Yes, toggle behavior
- Q: Should task updates support partial updates (PATCH semantics)? → A: Yes, partial updates allowed

---

## Actors

### Authenticated User

- A user who has successfully authenticated via JWT
- Identified uniquely by `user_id`
- Can only access their own data

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Task (Priority: P1)

As an authenticated user, I want to create a new task so that I can track work I need to complete.

**Why this priority**: Task creation is the foundational capability - without it, no other features are useful. Users must be able to add tasks to begin using the application.

**Independent Test**: Can be fully tested by creating a task with title and description, then verifying it appears in the user's task list with `completed = false`.

**Acceptance Scenarios**:

1. **Given** an authenticated user with valid JWT, **When** they submit a task with title "Buy groceries", **Then** the task is created with `completed = false` and a creation timestamp is recorded.
2. **Given** an authenticated user with valid JWT, **When** they submit a task with title "Call mom" and description "Discuss weekend plans", **Then** both title and description are stored and associated with the user.
3. **Given** an unauthenticated request (no JWT), **When** attempting to create a task, **Then** the system returns 401 Unauthorized.

---

### User Story 2 - View My Tasks (Priority: P1)

As an authenticated user, I want to view all my tasks so that I can see what I need to work on.

**Why this priority**: Viewing tasks is essential for the user to understand their workload. Tied with creation as the core functionality.

**Independent Test**: Can be fully tested by creating multiple tasks and verifying only the current user's tasks are returned.

**Acceptance Scenarios**:

1. **Given** an authenticated user with 3 existing tasks, **When** they request their task list, **Then** all 3 tasks are returned with their completion status.
2. **Given** an authenticated user with no tasks, **When** they request their task list, **Then** an empty list is returned.
3. **Given** two users A and B each with tasks, **When** user A requests their task list, **Then** only user A's tasks are returned (user isolation enforced).

---

### User Story 3 - Update a Task (Priority: P2)

As an authenticated user, I want to update my task's title or description so that I can correct mistakes or add details.

**Why this priority**: Updates allow users to refine task information, but the core value is already delivered by create/view.

**Independent Test**: Can be fully tested by creating a task, updating its title, and verifying the change persists.

**Acceptance Scenarios**:

1. **Given** an authenticated user with an existing task, **When** they update the title to "Buy groceries - organic only", **Then** the title is updated and an updated timestamp is recorded.
2. **Given** an authenticated user, **When** they attempt to update a task owned by another user, **Then** the system returns 403 Forbidden.
3. **Given** an authenticated user, **When** they attempt to update a non-existent task, **Then** the system returns 404 Not Found.

---

### User Story 4 - Toggle Task Completion (Priority: P2)

As an authenticated user, I want to toggle a task's completion status so that I can track my progress and reopen tasks if needed.

**Why this priority**: Completion tracking is a core productivity feature, enabling users to see what they've accomplished.

**Independent Test**: Can be fully tested by creating a task, marking it complete, then toggling it back to incomplete.

**Acceptance Scenarios**:

1. **Given** an authenticated user with an incomplete task, **When** they toggle completion, **Then** the task's `completed` status is set to `true`.
2. **Given** an authenticated user with a completed task, **When** they toggle completion, **Then** the task's `completed` status is set to `false`.
3. **Given** an authenticated user, **When** they attempt to toggle a task owned by another user, **Then** the system returns 403 Forbidden.

---

### User Story 5 - Delete a Task (Priority: P3)

As an authenticated user, I want to delete a task so that I can remove tasks I no longer need.

**Why this priority**: Deletion is useful for cleanup but not essential for core task management workflow.

**Independent Test**: Can be fully tested by creating a task, deleting it, and verifying it no longer appears in the task list.

**Acceptance Scenarios**:

1. **Given** an authenticated user with an existing task, **When** they delete the task, **Then** the task is permanently removed.
2. **Given** an authenticated user, **When** they attempt to delete a task owned by another user, **Then** the system returns 403 Forbidden.
3. **Given** an authenticated user, **When** they attempt to delete a non-existent task, **Then** the system returns 404 Not Found.

---

### Edge Cases

- What happens when a user submits a task with an empty title? System returns 422 Unprocessable Entity.
- What happens when a user submits a task with title exceeding 255 characters? System returns 422 Unprocessable Entity with validation error.
- What happens when a user submits a task with description exceeding 2000 characters? System returns 422 Unprocessable Entity with validation error.
- What happens when JWT token is expired? System returns 401 Unauthorized.
- What happens when JWT token is malformed? System returns 401 Unauthorized.
- What happens when user_id in URL does not match JWT user? System returns 403 Forbidden.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow authenticated users to create tasks with title (required) and description (optional).
- **FR-002**: System MUST associate each task with the authenticated user's `user_id`.
- **FR-003**: System MUST set `completed = false` for newly created tasks.
- **FR-004**: System MUST record creation timestamp when a task is created.
- **FR-005**: System MUST allow authenticated users to view only their own tasks.
- **FR-006**: System MUST return tasks as a list including completion status.
- **FR-007**: System MUST allow authenticated users to partially update title and/or description of their own tasks (PATCH semantics - only provided fields are updated).
- **FR-008**: System MUST record updated timestamp when a task is modified.
- **FR-009**: System MUST allow authenticated users to toggle completion status of their own tasks (complete ↔ incomplete).
- **FR-010**: System MUST allow authenticated users to delete their own tasks.
- **FR-011**: System MUST permanently remove deleted tasks.

### Authorization Requirements

- **AR-001**: All task operations MUST require a valid JWT token.
- **AR-002**: Requests without valid JWT MUST receive 401 Unauthorized.
- **AR-003**: Users MUST NOT access tasks owned by other users.
- **AR-004**: Cross-user access attempts MUST receive 403 Forbidden.
- **AR-005**: User identity MUST be derived from JWT, not client-provided identifiers.

### Error Handling Requirements

| Condition                       | Expected Response         |
|---------------------------------|---------------------------|
| Unauthenticated request         | 401 Unauthorized          |
| Accessing another user's task   | 403 Forbidden             |
| Task not found                  | 404 Not Found             |
| Invalid input (validation fail) | 422 Unprocessable Entity  |

### Key Entities

- **Task**: Represents a unit of work to be completed. Key attributes: id (UUID, system-generated), title (required, max 255 characters), description (optional, max 2000 characters), completed status, owner (user_id), creation timestamp, update timestamp.
- **User**: Represents an authenticated individual. Identified by unique `user_id` derived from JWT token.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a task and see it in their list within 2 seconds.
- **SC-002**: Users can complete all CRUD operations (create, read, update, delete) in a single session without errors.
- **SC-003**: 100% of cross-user access attempts are blocked with 403 Forbidden.
- **SC-004**: 100% of unauthenticated requests are blocked with 401 Unauthorized.
- **SC-005**: System correctly isolates user data - no user can see another user's tasks under any circumstance.
- **SC-006**: All task operations complete without blocking the user interface.

---

## Non-Functional Requirements

### Performance

- CRUD operations MUST complete within reasonable time (user perceives instant response).
- No blocking operations on request path.

### Security

- Stateless backend (no server-side sessions).
- JWT verification on every protected request.
- No sensitive data returned unintentionally.

### Maintainability

- Behavior MUST be spec-traceable.
- No hidden logic outside specifications.

---

## Out of Scope (Phase 2)

The following are explicitly excluded:

- Task sharing between users
- Task categories or tags
- Search or filtering capabilities
- Real-time updates (WebSockets)
- AI or chatbot features (Phase 3)
- Task due dates or reminders
- Task priorities or ordering

---

## Assumptions

- JWT authentication is handled by Better Auth on the frontend.
- Backend receives JWT tokens in Authorization header.
- User registration and login flows are separate features (authentication system).
- Task IDs are system-generated UUIDs (globally unique, non-sequential).
- No pagination required for Phase 2 (assumption: reasonable task count per user).

---

## Acceptance Criteria

The specification is satisfied when:

- All defined behaviors are implemented.
- No undocumented features exist.
- Authorization rules are enforced.
- System behavior matches this document exactly.

---

## Enforcement

Any ambiguity discovered during implementation:

- MUST halt execution.
- MUST be resolved by updating this specification.
