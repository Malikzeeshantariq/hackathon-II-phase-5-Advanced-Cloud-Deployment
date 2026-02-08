/**
 * T022: TaskList component.
 *
 * Spec Reference: US-2 (View Tasks)
 * Displays all tasks with Phase V filter/search/sort bar.
 */

"use client"

import { Task, TaskUpdate, TaskStatus, SortField, SortOrder } from "@/lib/types"
import TaskItem from "./TaskItem"

interface TaskListProps {
  tasks: Task[]
  userId: string
  onToggleComplete: (taskId: string) => Promise<void>
  onDelete: (taskId: string) => Promise<void>
  onUpdate: (taskId: string, data: TaskUpdate) => Promise<void>
  isLoading?: boolean
  error?: string | null
  // Filter/sort/search state
  searchTerm: string
  onSearchChange: (value: string) => void
  priorityFilter: string
  onPriorityFilterChange: (value: string) => void
  statusFilter: TaskStatus
  onStatusFilterChange: (value: TaskStatus) => void
  sortBy: SortField
  onSortByChange: (value: SortField) => void
  sortOrder: SortOrder
  onSortOrderChange: (value: SortOrder) => void
}

/**
 * Renders a list of tasks with filter/search/sort bar.
 */
export default function TaskList({
  tasks,
  userId,
  onToggleComplete,
  onDelete,
  onUpdate,
  isLoading = false,
  error = null,
  searchTerm,
  onSearchChange,
  priorityFilter,
  onPriorityFilterChange,
  statusFilter,
  onStatusFilterChange,
  sortBy,
  onSortByChange,
  sortOrder,
  onSortOrderChange,
}: TaskListProps) {
  const hasActiveFilters =
    searchTerm !== "" ||
    priorityFilter !== "" ||
    statusFilter !== "all" ||
    sortBy !== "created_at" ||
    sortOrder !== "desc"

  const showFilterBar = tasks.length > 0 || hasActiveFilters

  // Loading state
  if (isLoading && !showFilterBar) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        <p className="font-medium">Error loading tasks</p>
        <p className="text-sm">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filter/Search/Sort bar */}
      {showFilterBar && (
        <div className="space-y-3 bg-gray-50 rounded-lg p-4 border border-gray-200">
          {/* Search */}
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search tasks..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
          />

          {/* Filter row */}
          <div className="flex flex-wrap gap-2">
            {/* Priority filter */}
            <select
              value={priorityFilter}
              onChange={(e) => onPriorityFilterChange(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
            >
              <option value="">All priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            {/* Status filter */}
            <select
              value={statusFilter}
              onChange={(e) => onStatusFilterChange(e.target.value as TaskStatus)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
            >
              <option value="all">All status</option>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
            </select>

            {/* Sort by */}
            <select
              value={sortBy}
              onChange={(e) => onSortByChange(e.target.value as SortField)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
            >
              <option value="created_at">Sort: Created</option>
              <option value="due_at">Sort: Due date</option>
              <option value="priority">Sort: Priority</option>
              <option value="title">Sort: Title</option>
            </select>

            {/* Sort order toggle */}
            <button
              onClick={() => onSortOrderChange(sortOrder === "asc" ? "desc" : "asc")}
              className="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-100 bg-white text-sm transition-colors"
              aria-label={`Sort ${sortOrder === "asc" ? "descending" : "ascending"}`}
            >
              {sortOrder === "asc" ? (
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                  </svg>
                  Asc
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
                  </svg>
                  Desc
                </span>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Loading overlay when filters change */}
      {isLoading && showFilterBar && (
        <div className="flex justify-center items-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && tasks.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            {hasActiveFilters ? "No matching tasks" : "No tasks"}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {hasActiveFilters
              ? "Try adjusting your filters or search term."
              : "Get started by creating a new task."}
          </p>
        </div>
      )}

      {/* Task items */}
      {!isLoading && tasks.length > 0 && (
        <div className="space-y-3">
          {tasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              userId={userId}
              onToggleComplete={onToggleComplete}
              onDelete={onDelete}
              onUpdate={onUpdate}
            />
          ))}
        </div>
      )}
    </div>
  )
}
