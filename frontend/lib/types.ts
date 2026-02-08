/**
 * T015: TypeScript type definitions.
 *
 * Spec Reference: contracts/openapi.yaml - schemas
 * Spec Reference: data-model.md - Entities
 * Phase V: priority, tags, due_at, is_recurring, recurrence_rule, reminders
 */

export type Priority = "low" | "medium" | "high" | "critical"
export type TaskStatus = "completed" | "pending" | "all"
export type SortField = "created_at" | "due_at" | "priority" | "title"
export type SortOrder = "asc" | "desc"

/**
 * Task entity as returned by the API.
 *
 * Spec Reference: TaskResponse schema in openapi.yaml
 */
export interface Task {
  id: string
  title: string
  description: string | null
  completed: boolean
  priority: string | null
  tags: string[]
  due_at: string | null
  is_recurring: boolean
  recurrence_rule: string | null
  created_at: string
  updated_at: string
}

/**
 * Request body for creating a task.
 *
 * Spec Reference: TaskCreate schema in openapi.yaml
 */
export interface TaskCreate {
  title: string
  description?: string | null
  priority?: string | null
  tags?: string[]
  due_at?: string | null
  is_recurring?: boolean
  recurrence_rule?: string | null
}

/**
 * Request body for updating a task.
 *
 * Spec Reference: TaskUpdate schema in openapi.yaml
 */
export interface TaskUpdate {
  title?: string
  description?: string | null
  priority?: string | null
  tags?: string[]
  due_at?: string | null
  is_recurring?: boolean
  recurrence_rule?: string | null
}

/**
 * Query parameters for listing tasks with filter/sort/search.
 */
export interface TaskListParams {
  priority?: Priority
  status?: TaskStatus
  search?: string
  sort_by?: SortField
  sort_order?: SortOrder
  due_before?: string
  due_after?: string
  tags?: string
}

/**
 * Response body for listing tasks.
 *
 * Spec Reference: TaskListResponse schema in openapi.yaml
 */
export interface TaskListResponse {
  tasks: Task[]
}

/**
 * User information from auth session.
 */
export interface User {
  id: string
  email: string
  name?: string
}

/**
 * Reminder entity as returned by the API.
 */
export interface Reminder {
  id: string
  task_id: string
  user_id: string
  remind_at: string
  created_at: string
}

/**
 * Request body for creating a reminder.
 */
export interface ReminderCreate {
  remind_at: string
}

/**
 * API error response format.
 *
 * Spec Reference: ErrorResponse schema in openapi.yaml
 */
export interface ApiError {
  detail: string
}

/**
 * Validation error response format.
 *
 * Spec Reference: ValidationErrorResponse schema in openapi.yaml
 */
export interface ValidationError {
  detail: Array<{
    loc: string[]
    msg: string
    type: string
  }>
}
