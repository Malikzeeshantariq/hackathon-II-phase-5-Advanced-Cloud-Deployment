/**
 * T014: API client with JWT headers.
 *
 * Spec Reference: plan.md - Request Flow
 * Spec Reference: AR-001 - JWT token in Authorization header
 * Phase V: filter/sort/search params, reminder endpoints
 */

import axios, { AxiosInstance, AxiosError } from "axios"
import { getAuthToken } from "./auth"
import type {
  Task,
  TaskCreate,
  TaskUpdate,
  TaskListResponse,
  TaskListParams,
  Reminder,
  ReminderCreate,
} from "./types"

// In production, use relative URL so requests go through Next.js rewrites proxy.
// In development, use NEXT_PUBLIC_API_URL to hit the backend directly.
const API_BASE_URL = process.env.NODE_ENV === "production" ? "" : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")

/**
 * Create an Axios instance with JWT authentication.
 *
 * The interceptor automatically attaches the JWT token
 * to every request's Authorization header.
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor to attach JWT token
apiClient.interceptors.request.use(
  async (config) => {
    const token = await getAuthToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      if (typeof window !== "undefined") {
        window.location.href = "/login"
      }
    }
    return Promise.reject(error)
  }
)

/**
 * Task API endpoints.
 *
 * All endpoints require JWT authentication and enforce
 * user isolation (users can only access their own tasks).
 */
export const taskApi = {
  /**
   * List all tasks for a user with optional filter/sort/search.
   * Spec Reference: FR-005, FR-006, FR-007, FR-008
   */
  async listTasks(userId: string, params?: TaskListParams): Promise<Task[]> {
    const response = await apiClient.get<TaskListResponse>(
      `/api/${userId}/tasks`,
      { params }
    )
    return response.data.tasks
  },

  /**
   * Get a single task by ID.
   * Spec Reference: FR-005
   */
  async getTask(userId: string, taskId: string): Promise<Task> {
    const response = await apiClient.get<Task>(
      `/api/${userId}/tasks/${taskId}`
    )
    return response.data
  },

  /**
   * Create a new task.
   * Spec Reference: FR-001 to FR-004
   */
  async createTask(userId: string, data: TaskCreate): Promise<Task> {
    const response = await apiClient.post<Task>(
      `/api/${userId}/tasks`,
      data
    )
    return response.data
  },

  /**
   * Update an existing task.
   * Spec Reference: FR-007, FR-008
   */
  async updateTask(
    userId: string,
    taskId: string,
    data: TaskUpdate
  ): Promise<Task> {
    const response = await apiClient.put<Task>(
      `/api/${userId}/tasks/${taskId}`,
      data
    )
    return response.data
  },

  /**
   * Delete a task.
   * Spec Reference: FR-010, FR-011
   */
  async deleteTask(userId: string, taskId: string): Promise<void> {
    await apiClient.delete(`/api/${userId}/tasks/${taskId}`)
  },

  /**
   * Toggle task completion status.
   * Spec Reference: FR-009
   */
  async toggleComplete(userId: string, taskId: string): Promise<Task> {
    const response = await apiClient.patch<Task>(
      `/api/${userId}/tasks/${taskId}/complete`
    )
    return response.data
  },

  /**
   * List reminders for a task.
   */
  async listReminders(
    userId: string,
    taskId: string
  ): Promise<Reminder[]> {
    const response = await apiClient.get<Reminder[]>(
      `/api/${userId}/tasks/${taskId}/reminders`
    )
    return response.data
  },

  /**
   * Create a reminder for a task.
   */
  async createReminder(
    userId: string,
    taskId: string,
    data: ReminderCreate
  ): Promise<Reminder> {
    const response = await apiClient.post<Reminder>(
      `/api/${userId}/tasks/${taskId}/reminders`,
      data
    )
    return response.data
  },

  /**
   * Delete a reminder.
   */
  async deleteReminder(
    userId: string,
    taskId: string,
    reminderId: string
  ): Promise<void> {
    await apiClient.delete(
      `/api/${userId}/tasks/${taskId}/reminders/${reminderId}`
    )
  },
}

export default apiClient
