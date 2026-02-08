# Implementation Tasks: Todo AI Chatbot (Phase 3)

**Feature**: Todo AI Chatbot (Phase 3)
**Branch**: `001-todo-ai-chatbot` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-todo-ai-chatbot/spec.md`
**Governed By**: Phase 3 Constitution v2.0.0

## Implementation Strategy

Build the AI-powered conversational interface for the Todo application following a phased approach:
- MVP: Basic chat functionality with task creation (User Story 1)
- Incremental: Add remaining user stories in priority order (P1, P2, P3...)
- Polish: Cross-cutting concerns and integration testing

## Dependencies

- Phase 2 authentication system (Better Auth, JWT) - DONE
- Phase 2 task data model and API - DONE
- PostgreSQL (Neon Serverless) - DONE
- OpenAI Agents SDK and MCP tools - SETUP NEEDED

## Parallel Execution Examples

### User Story 1 (P1): Create Task via Chat
- Backend: Chat endpoint, MCP tools, conversation models
- Frontend: Chat UI, API client integration
- Both can be developed in parallel after foundational setup

### User Story 2 (P1): List Tasks via Chat
- Can be implemented after US1 foundation is established
- Uses same chat infrastructure with different MCP tool

## Phase 1: Setup Tasks

### Project Initialization
- [X] T001 Create backend directory structure per plan
- [X] T002 Add MCP dependencies to backend requirements.txt
- [X] T003 Create frontend directory structure per plan
- [X] T004 Add ChatKit dependencies to frontend package.json

## Phase 2: Foundational Tasks

### Database Models
- [X] T005 [P] Create conversation model in backend/app/models/conversation.py
- [X] T006 [P] Create message model in backend/app/models/message.py
- [X] T007 [P] Create tool_call model in backend/app/models/tool_call.py
- [ ] T008 [P] Update database migration files for new tables

### MCP Tools Foundation
- [X] T009 [P] Create MCP server foundation in backend/app/mcp/server.py
- [X] T010 [P] Create add_task MCP tool in backend/app/mcp/tools/add_task.py
- [X] T011 [P] Create list_tasks MCP tool in backend/app/mcp/tools/list_tasks.py
- [X] T012 [P] Create complete_task MCP tool in backend/app/mcp/tools/complete_task.py
- [X] T013 [P] Create delete_task MCP tool in backend/app/mcp/tools/delete_task.py
- [X] T014 [P] Create update_task MCP tool in backend/app/mcp/tools/update_task.py

### Services
- [X] T015 Create agent service in backend/app/services/agent_service.py
- [X] T016 Create chat service in backend/app/services/chat_service.py

## Phase 3: User Story 1 - Create Task via Chat (Priority: P1)

**Goal**: Enable users to quickly add new tasks by typing natural language commands.

**Independent Test**: User sends "Add a task to buy groceries" and receives confirmation with the created task details.

### Acceptance Scenarios Implementation:
1. **Natural language task creation with confirmation**
2. **Full task creation with title and description**
3. **Clarification request for incomplete input**

### Implementation Tasks:
- [X] T017 [US1] Implement add_task MCP tool with validation
- [X] T018 [US1] Create chat endpoint in backend/app/routers/chat.py
- [X] T019 [US1] Implement chat service logic for task creation
- [X] T020 [US1] Integrate agent service with MCP tools
- [X] T021 [US1] Create frontend ChatPanel component in frontend/components/ChatPanel.tsx
- [X] T022 [US1] Implement chat API client in frontend/lib/chat-client.ts
- [X] T023 [US1] Create chat page in frontend/app/chat/page.tsx
- [ ] T024 [US1] Test scenario: Create task with "Add a task to buy groceries"

## Phase 4: User Story 2 - List Tasks via Chat (Priority: P1)

**Goal**: Enable users to view their tasks by asking the assistant.

**Independent Test**: User sends "Show my tasks" and receives a formatted list of their tasks.

### Acceptance Scenarios Implementation:
1. **Display all tasks for user**
2. **Display only pending tasks**
3. **Display only completed tasks**
4. **Handle case with no tasks**

### Implementation Tasks:
- [X] T025 [US2] Implement list_tasks MCP tool with filtering
- [X] T026 [US2] Enhance chat service to handle list operations
- [X] T027 [US2] Update agent service to recognize list intents
- [ ] T028 [US2] Test scenario: Show all tasks with "Show my tasks"
- [ ] T029 [US2] Test scenario: Show pending tasks with "What tasks are pending?"
- [ ] T030 [US2] Test scenario: Handle empty task list

## Phase 5: User Story 3 - Complete Task via Chat (Priority: P2)

**Goal**: Enable users to mark tasks as done through conversation.

**Independent Test**: User sends "Mark 'buy groceries' as done" and receives confirmation.

### Acceptance Scenarios Implementation:
1. **Complete specific task by title**
2. **Identify and complete matching task**
3. **Ask for clarification when task is not specified**
4. **Handle case with non-existent task**

### Implementation Tasks:
- [X] T031 [US3] Implement complete_task MCP tool with validation
- [X] T032 [US3] Enhance chat service to handle completion operations
- [X] T033 [US3] Update agent service to recognize completion intents
- [ ] T034 [US3] Test scenario: Complete task with "Complete buy groceries"
- [ ] T035 [US3] Test scenario: Handle ambiguous task reference

## Phase 6: User Story 4 - Delete Task via Chat (Priority: P2)

**Goal**: Enable users to remove tasks they no longer need.

**Independent Test**: User sends "Delete the groceries task" and receives confirmation of deletion.

### Acceptance Scenarios Implementation:
1. **Delete specific task by title**
2. **Handle bulk deletion clarification**
3. **Handle non-existent task reference**

### Implementation Tasks:
- [X] T036 [US4] Implement delete_task MCP tool with validation
- [X] T037 [US4] Enhance chat service to handle deletion operations
- [X] T038 [US4] Update agent service to recognize deletion intents
- [ ] T039 [US4] Test scenario: Delete task with "Delete buy groceries"
- [ ] T040 [US4] Test scenario: Handle bulk deletion request

## Phase 7: User Story 5 - Update Task via Chat (Priority: P3)

**Goal**: Enable users to modify existing task's details.

**Independent Test**: User sends "Rename 'groceries' to 'weekly grocery shopping'" and receives confirmation.

### Acceptance Scenarios Implementation:
1. **Update task title**
2. **Update task description**
3. **Ask for clarification when update details are missing**

### Implementation Tasks:
- [X] T041 [US5] Implement update_task MCP tool with validation
- [X] T042 [US5] Enhance chat service to handle update operations
- [X] T043 [US5] Update agent service to recognize update intents
- [ ] T044 [US5] Test scenario: Update task title with "Rename groceries to weekly shopping"
- [ ] T045 [US5] Test scenario: Update task description

## Phase 8: User Story 6 - Persistent Conversation (Priority: P2)

**Goal**: Ensure conversation history persists across sessions.

**Independent Test**: User closes browser, returns later, and previous messages are visible.

### Acceptance Scenarios Implementation:
1. **Restore conversation history**
2. **Create new conversation for first-time users**
3. **Maintain history after server restart**

### Implementation Tasks:
- [X] T046 [US6] Implement conversation persistence in chat service
- [X] T047 [US6] Create get_or_create_conversation function
- [X] T048 [US6] Implement conversation loading with history
- [X] T049 [US6] Add conversation listing endpoint
- [X] T050 [US6] Add conversation retrieval endpoint
- [X] T051 [US6] Add conversation deletion endpoint
- [ ] T052 [US6] Test scenario: Restore conversation after browser close

## Phase 9: Edge Cases & Error Handling

### Implementation Tasks:
- [X] T053 Handle ambiguous user input with clarification requests
- [X] T054 Handle multiple matching tasks with disambiguation
- [X] T055 Handle AI inability to interpret intent with helpful suggestions
- [X] T056 Handle tool operation failures with clear user messaging
- [X] T057 Handle cross-user access attempts with appropriate errors
- [X] T058 Implement user isolation validation in all MCP tools

## Phase 10: Polish & Cross-Cutting Concerns

### Security & Validation
- [X] T059 Validate all MCP tools enforce user ownership
- [X] T060 Verify JWT authentication on all endpoints
- [X] T061 Test user isolation (ensure no cross-user access)
- [X] T062 Validate input sanitization in all endpoints

### Performance & Monitoring
- [ ] T063 Add logging for tool calls and AI interactions
- [ ] T064 Implement response time monitoring for chat operations
- [ ] T065 Add error tracking for failed tool operations

### Testing & Quality
- [ ] T066 Create integration tests for all user stories
- [ ] T067 Create unit tests for MCP tools
- [ ] T068 Test conversation persistence across restarts
- [ ] T069 Test stateless architecture compliance

### Documentation & Deployment
- [ ] T070 Update API documentation based on final implementation
- [ ] T071 Create deployment configuration for MCP server
- [ ] T072 Add environment configuration for OpenAI/MCP integration
- [ ] T073 Create user documentation for chat functionality

## MVP Scope (Recommended for Initial Delivery)

Focus on User Story 1 (task creation) to establish the core chat infrastructure:
- T001-T016 (Foundational setup)
- T017-T024 (Task creation functionality)
- T059-T062 (Security validation)
- T070-T073 (Documentation and deployment)

This provides a complete, testable chat system that can create tasks, which can then be extended with additional functionality in subsequent iterations.