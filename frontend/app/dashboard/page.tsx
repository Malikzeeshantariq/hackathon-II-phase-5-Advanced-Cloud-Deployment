/**
 * T025: Dashboard page.
 *
 * Spec Reference: US-1 (Create), US-2 (View)
 * Main task management interface with Phase V filter/sort/search.
 */

"use client"

import { useState, useEffect, useCallback } from "react"
import { useSession } from "@/lib/auth"
import { taskApi } from "@/lib/api-client"
import type { Task, TaskCreate, TaskUpdate, TaskListParams, TaskStatus, SortField, SortOrder } from "@/lib/types"
import TaskList from "@/components/TaskList"
import TaskForm from "@/components/TaskForm"
import { useTaskRefresh } from "./layout"

/**
 * Dashboard page for task management with Phase V features.
 */
export default function DashboardPage() {
  const { data: session } = useSession()
  const { refreshKey } = useTaskRefresh()
  const [tasks, setTasks] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  // Filter/sort/search state
  const [searchTerm, setSearchTerm] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [priorityFilter, setPriorityFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState<TaskStatus>("all")
  const [sortBy, setSortBy] = useState<SortField>("created_at")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")

  const userId = session?.user?.id

  // Debounce search with 300ms delay
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchTerm])

  // Fetch tasks with filters
  const fetchTasks = useCallback(async () => {
    if (!userId) return

    setIsLoading(true)
    setError(null)

    try {
      const params: TaskListParams = {
        sort_by: sortBy,
        sort_order: sortOrder,
      }
      if (debouncedSearch) params.search = debouncedSearch
      if (priorityFilter) params.priority = priorityFilter as TaskListParams["priority"]
      if (statusFilter !== "all") params.status = statusFilter

      const fetchedTasks = await taskApi.listTasks(userId, params)
      setTasks(fetchedTasks)
    } catch (err) {
      console.error("Failed to fetch tasks:", err)
      setError("Failed to load tasks. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }, [userId, debouncedSearch, priorityFilter, statusFilter, sortBy, sortOrder])

  // Fetch tasks on mount, filter change, and refreshKey change
  useEffect(() => {
    fetchTasks()
  }, [fetchTasks, refreshKey])

  // Create task handler
  const handleCreateTask = async (data: TaskCreate) => {
    if (!userId) return

    setIsCreating(true)
    setCreateError(null)

    try {
      const newTask = await taskApi.createTask(userId, data)
      setTasks((prev) => [newTask, ...prev])
    } catch (err: unknown) {
      console.error("Failed to create task:", err)
      const error = err as { response?: { data?: { detail?: string } } }
      setCreateError(error.response?.data?.detail || "Failed to create task")
      throw err
    } finally {
      setIsCreating(false)
    }
  }

  // Toggle completion handler
  const handleToggleComplete = async (taskId: string) => {
    if (!userId) return

    try {
      const updatedTask = await taskApi.toggleComplete(userId, taskId)
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? updatedTask : t))
      )
    } catch (err) {
      console.error("Failed to toggle task:", err)
      setError("Failed to update task. Please try again.")
    }
  }

  // Update task handler
  const handleUpdateTask = async (taskId: string, data: TaskUpdate) => {
    if (!userId) return

    try {
      const updatedTask = await taskApi.updateTask(userId, taskId, data)
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? updatedTask : t))
      )
    } catch (err) {
      console.error("Failed to update task:", err)
      setError("Failed to update task. Please try again.")
      throw err
    }
  }

  // Delete task handler
  const handleDeleteTask = async (taskId: string) => {
    if (!userId) return

    try {
      await taskApi.deleteTask(userId, taskId)
      setTasks((prev) => prev.filter((t) => t.id !== taskId))
    } catch (err) {
      console.error("Failed to delete task:", err)
      setError("Failed to delete task. Please try again.")
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">My Tasks</h1>
        <p className="text-gray-600 mt-1">
          Manage your tasks and stay organized
        </p>
      </div>

      {/* Create task form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Create New Task
        </h2>
        <TaskForm
          onSubmit={handleCreateTask}
          isSubmitting={isCreating}
          error={createError}
        />
      </div>

      {/* Task list with filters */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Your Tasks {!isLoading && `(${tasks.length})`}
        </h2>
        <TaskList
          tasks={tasks}
          userId={userId!}
          onToggleComplete={handleToggleComplete}
          onDelete={handleDeleteTask}
          onUpdate={handleUpdateTask}
          isLoading={isLoading}
          error={error}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          priorityFilter={priorityFilter}
          onPriorityFilterChange={setPriorityFilter}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          sortBy={sortBy}
          onSortByChange={setSortBy}
          sortOrder={sortOrder}
          onSortOrderChange={setSortOrder}
        />
      </div>
    </div>
  )
}
