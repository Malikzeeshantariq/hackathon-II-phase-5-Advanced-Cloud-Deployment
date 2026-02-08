/**
 * T024, T029, T030, T033: TaskItem component.
 *
 * Spec Reference: US-2 (View), US-3 (Update), US-4 (Complete), US-5 (Delete)
 * Individual task display with Phase V fields, reminders, and all CRUD actions.
 */

"use client"

import { useState, KeyboardEvent } from "react"
import { Task, TaskUpdate, Reminder } from "@/lib/types"
import { taskApi } from "@/lib/api-client"

const PRIORITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-gray-100 text-gray-600",
}

interface TaskItemProps {
  task: Task
  userId: string
  onToggleComplete: (taskId: string) => Promise<void>
  onDelete: (taskId: string) => Promise<void>
  onUpdate: (taskId: string, data: TaskUpdate) => Promise<void>
}

function formatDueDate(due_at: string | null, completed: boolean) {
  if (!due_at) return null
  const date = new Date(due_at)
  const now = new Date()
  const isOverdue = date < now && !completed
  const formatted = date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
    hour: "numeric",
    minute: "2-digit",
  })
  return { formatted, isOverdue }
}

/**
 * Renders a single task with Phase V fields, reminders, and actions.
 */
export default function TaskItem({
  task,
  userId,
  onToggleComplete,
  onDelete,
  onUpdate,
}: TaskItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(task.title)
  const [editDescription, setEditDescription] = useState(task.description || "")
  const [editPriority, setEditPriority] = useState(task.priority || "")
  const [editTags, setEditTags] = useState<string[]>(task.tags || [])
  const [editTagInput, setEditTagInput] = useState("")
  const [editDueAt, setEditDueAt] = useState(() => {
    if (!task.due_at) return ""
    const d = new Date(task.due_at)
    return d.toISOString().slice(0, 16)
  })
  const [editIsRecurring, setEditIsRecurring] = useState(task.is_recurring)
  const [editRecurrenceRule, setEditRecurrenceRule] = useState(task.recurrence_rule || "")
  const [isLoading, setIsLoading] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  // Reminder state
  const [showReminders, setShowReminders] = useState(false)
  const [reminders, setReminders] = useState<Reminder[]>([])
  const [remindersLoading, setRemindersLoading] = useState(false)
  const [reminderInput, setReminderInput] = useState("")
  const [reminderError, setReminderError] = useState<string | null>(null)

  const handleToggleComplete = async () => {
    setIsLoading(true)
    try {
      await onToggleComplete(task.id)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStartEdit = () => {
    setEditTitle(task.title)
    setEditDescription(task.description || "")
    setEditPriority(task.priority || "")
    setEditTags(task.tags || [])
    setEditTagInput("")
    setEditDueAt(task.due_at ? new Date(task.due_at).toISOString().slice(0, 16) : "")
    setEditIsRecurring(task.is_recurring)
    setEditRecurrenceRule(task.recurrence_rule || "")
    setIsEditing(true)
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
  }

  const handleAddEditTag = () => {
    const trimmed = editTagInput.trim()
    if (trimmed && !editTags.includes(trimmed)) {
      setEditTags((prev) => [...prev, trimmed])
    }
    setEditTagInput("")
  }

  const handleEditTagKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault()
      handleAddEditTag()
    }
  }

  const handleSaveEdit = async () => {
    const trimmedTitle = editTitle.trim()
    if (!trimmedTitle) return

    setIsLoading(true)
    try {
      const data: TaskUpdate = {
        title: trimmedTitle,
        description: editDescription.trim() || null,
        priority: editPriority || null,
        tags: editTags,
        due_at: editDueAt ? new Date(editDueAt).toISOString() : null,
        is_recurring: editIsRecurring,
        recurrence_rule: editIsRecurring ? editRecurrenceRule : null,
      }
      await onUpdate(task.id, data)
      setIsEditing(false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this task?")) return
    setIsDeleting(true)
    try {
      await onDelete(task.id)
    } finally {
      setIsDeleting(false)
    }
  }

  // Reminder handlers
  const handleToggleReminders = async () => {
    if (!showReminders) {
      setRemindersLoading(true)
      setReminderError(null)
      try {
        const data = await taskApi.listReminders(userId, task.id)
        setReminders(data)
      } catch {
        setReminderError("Failed to load reminders")
      } finally {
        setRemindersLoading(false)
      }
    }
    setShowReminders(!showReminders)
  }

  const handleAddReminder = async () => {
    if (!reminderInput) return
    setReminderError(null)
    try {
      const reminder = await taskApi.createReminder(userId, task.id, {
        remind_at: new Date(reminderInput).toISOString(),
      })
      setReminders((prev) => [...prev, reminder].sort((a, b) => a.remind_at.localeCompare(b.remind_at)))
      setReminderInput("")
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setReminderError(error.response?.data?.detail || "Failed to create reminder")
    }
  }

  const handleDeleteReminder = async (reminderId: string) => {
    try {
      await taskApi.deleteReminder(userId, task.id, reminderId)
      setReminders((prev) => prev.filter((r) => r.id !== reminderId))
    } catch {
      setReminderError("Failed to delete reminder")
    }
  }

  const dueInfo = formatDueDate(task.due_at, task.completed)

  // Edit mode view
  if (isEditing) {
    return (
      <div className="bg-white border border-blue-200 rounded-lg p-4 shadow-sm">
        <div className="space-y-3">
          <input
            type="text"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            placeholder="Task title"
            maxLength={255}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            autoFocus
          />
          <textarea
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            placeholder="Description (optional)"
            maxLength={10000}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y"
          />

          {/* Priority & Due Date */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <select
              value={editPriority}
              onChange={(e) => setEditPriority(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="">Priority: none</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
            <input
              type="datetime-local"
              value={editDueAt}
              onChange={(e) => setEditDueAt(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>

          {/* Tags */}
          <div>
            <input
              type="text"
              value={editTagInput}
              onChange={(e) => setEditTagInput(e.target.value)}
              onKeyDown={handleEditTagKeyDown}
              onBlur={handleAddEditTag}
              placeholder="Add tag, press Enter"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
            {editTags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {editTags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-700"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => setEditTags((prev) => prev.filter((t) => t !== tag))}
                      className="hover:text-blue-900"
                    >
                      &times;
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Recurrence */}
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={editIsRecurring}
              onChange={(e) => {
                setEditIsRecurring(e.target.checked)
                if (!e.target.checked) setEditRecurrenceRule("")
              }}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Recurring
          </label>
          {editIsRecurring && (
            <select
              value={editRecurrenceRule}
              onChange={(e) => setEditRecurrenceRule(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="">Select frequency</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleSaveEdit}
              disabled={isLoading || !editTitle.trim()}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? "Saving..." : "Save"}
            </button>
            <button
              onClick={handleCancelEdit}
              disabled={isLoading}
              className="px-4 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Normal view
  return (
    <div
      className={`bg-white border rounded-lg p-4 shadow-sm transition-all ${
        task.completed ? "border-green-200 bg-green-50" : "border-gray-200"
      } ${isDeleting ? "opacity-50" : ""}`}
    >
      <div className="flex items-start gap-3">
        {/* Completion checkbox */}
        <button
          onClick={handleToggleComplete}
          disabled={isLoading || isDeleting}
          className={`flex-shrink-0 w-6 h-6 mt-0.5 rounded-full border-2 flex items-center justify-center transition-colors ${
            task.completed
              ? "bg-green-500 border-green-500 text-white"
              : "border-gray-300 hover:border-green-400"
          } ${isLoading ? "opacity-50 cursor-wait" : ""}`}
          aria-label={task.completed ? "Mark as incomplete" : "Mark as complete"}
        >
          {task.completed && (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          )}
        </button>

        {/* Task content */}
        <div className="flex-grow min-w-0">
          <h3
            className={`font-medium text-gray-900 ${
              task.completed ? "line-through text-gray-500" : ""
            }`}
          >
            {task.title}
          </h3>
          {task.description && (
            <p
              className={`mt-1 text-sm ${
                task.completed ? "text-gray-400" : "text-gray-600"
              }`}
            >
              {task.description}
            </p>
          )}

          {/* Phase V metadata row */}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {task.priority && (
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                  PRIORITY_STYLES[task.priority] || "bg-gray-100 text-gray-600"
                }`}
              >
                {task.priority}
              </span>
            )}

            {task.tags?.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700"
              >
                {tag}
              </span>
            ))}

            {dueInfo && (
              <span
                className={`text-xs ${
                  dueInfo.isOverdue
                    ? "text-red-600 font-medium"
                    : "text-gray-500"
                }`}
              >
                {dueInfo.isOverdue ? "Overdue: " : "Due: "}
                {dueInfo.formatted}
              </span>
            )}

            {task.is_recurring && task.recurrence_rule && (
              <span className="inline-flex items-center gap-1 text-xs text-purple-600">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {task.recurrence_rule}
              </span>
            )}
          </div>

          <p className="mt-1.5 text-xs text-gray-400">
            Created: {new Date(task.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex-shrink-0 flex gap-1">
          {/* Reminder bell button */}
          <button
            onClick={handleToggleReminders}
            disabled={isDeleting}
            className={`p-2 rounded-lg transition-colors disabled:opacity-50 ${
              showReminders
                ? "text-amber-600 bg-amber-50"
                : "text-gray-400 hover:text-amber-600 hover:bg-amber-50"
            }`}
            aria-label="Reminders"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>
          {/* Edit button */}
          <button
            onClick={handleStartEdit}
            disabled={isDeleting}
            className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
            aria-label="Edit task"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
          </button>
          {/* Delete button */}
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            aria-label="Delete task"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Reminders panel */}
      {showReminders && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <h4 className="text-xs font-medium text-gray-700 mb-2">Reminders</h4>

          {reminderError && (
            <p className="text-xs text-red-600 mb-2">{reminderError}</p>
          )}

          {remindersLoading ? (
            <div className="flex items-center gap-2 text-xs text-gray-400 py-1">
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-400"></div>
              Loading...
            </div>
          ) : (
            <>
              {reminders.length === 0 && (
                <p className="text-xs text-gray-400 mb-2">No reminders set.</p>
              )}
              {reminders.map((r) => {
                const rDate = new Date(r.remind_at)
                const isPast = rDate < new Date()
                return (
                  <div key={r.id} className="flex items-center justify-between py-1">
                    <span className={`text-xs ${isPast ? "text-gray-400 line-through" : "text-gray-700"}`}>
                      {rDate.toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "numeric",
                        minute: "2-digit",
                      })}
                    </span>
                    <button
                      onClick={() => handleDeleteReminder(r.id)}
                      className="text-gray-400 hover:text-red-500 p-0.5"
                      aria-label="Delete reminder"
                    >
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                )
              })}
            </>
          )}

          {/* Add reminder */}
          <div className="flex gap-2 mt-2">
            <input
              type="datetime-local"
              value={reminderInput}
              onChange={(e) => setReminderInput(e.target.value)}
              className="flex-grow px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            />
            <button
              onClick={handleAddReminder}
              disabled={!reminderInput}
              className="px-2 py-1 bg-amber-500 text-white text-xs rounded hover:bg-amber-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Add
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
