/**
 * T023: TaskForm component.
 *
 * Spec Reference: US-1 (Create Task)
 * Form for creating new tasks with Phase V fields:
 * title, description, priority, tags, due date, recurrence.
 */

"use client"

import { useState, FormEvent, KeyboardEvent } from "react"
import type { TaskCreate } from "@/lib/types"

interface TaskFormProps {
  onSubmit: (data: TaskCreate) => Promise<void>
  isSubmitting?: boolean
  error?: string | null
}

/**
 * Form for creating new tasks with Phase V fields.
 */
export default function TaskForm({
  onSubmit,
  isSubmitting = false,
  error = null,
}: TaskFormProps) {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [priority, setPriority] = useState("")
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState("")
  const [dueAt, setDueAt] = useState("")
  const [isRecurring, setIsRecurring] = useState(false)
  const [recurrenceRule, setRecurrenceRule] = useState("")
  const [localError, setLocalError] = useState<string | null>(null)

  const handleAddTag = () => {
    const trimmed = tagInput.trim()
    if (trimmed && !tags.includes(trimmed)) {
      setTags((prev) => [...prev, trimmed])
    }
    setTagInput("")
  }

  const handleTagKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault()
      handleAddTag()
    }
  }

  const handleRemoveTag = (tag: string) => {
    setTags((prev) => prev.filter((t) => t !== tag))
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    const trimmedTitle = title.trim()
    if (!trimmedTitle) {
      setLocalError("Title is required")
      return
    }
    if (trimmedTitle.length > 255) {
      setLocalError("Title must be 255 characters or less")
      return
    }
    if (description.length > 10000) {
      setLocalError("Description must be 10000 characters or less")
      return
    }
    if (isRecurring && !recurrenceRule) {
      setLocalError("Recurrence rule is required when recurring is enabled")
      return
    }

    const data: TaskCreate = {
      title: trimmedTitle,
      description: description.trim() || null,
    }
    if (priority) data.priority = priority
    if (tags.length > 0) data.tags = tags
    if (dueAt) data.due_at = new Date(dueAt).toISOString()
    if (isRecurring) {
      data.is_recurring = true
      data.recurrence_rule = recurrenceRule
    }

    try {
      await onSubmit(data)
      // Reset all fields on success
      setTitle("")
      setDescription("")
      setPriority("")
      setTags([])
      setTagInput("")
      setDueAt("")
      setIsRecurring(false)
      setRecurrenceRule("")
    } catch {
      // Error handled by parent
    }
  }

  const displayError = localError || error

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {displayError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {displayError}
        </div>
      )}

      {/* Title */}
      <div>
        <label
          htmlFor="title"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Title <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="What needs to be done?"
          maxLength={255}
          required
          disabled={isSubmitting}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
        <p className="mt-1 text-xs text-gray-500">
          {title.length}/255 characters
        </p>
      </div>

      {/* Description */}
      <div>
        <label
          htmlFor="description"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Add more details (optional)"
          maxLength={10000}
          rows={3}
          disabled={isSubmitting}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed resize-y"
        />
      </div>

      {/* Priority & Due Date row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label
            htmlFor="priority"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Priority
          </label>
          <select
            id="priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            disabled={isSubmitting}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">(none)</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        <div>
          <label
            htmlFor="dueAt"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Due Date
          </label>
          <input
            type="datetime-local"
            id="dueAt"
            value={dueAt}
            onChange={(e) => setDueAt(e.target.value)}
            disabled={isSubmitting}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
        </div>
      </div>

      {/* Tags */}
      <div>
        <label
          htmlFor="tagInput"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Tags
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            id="tagInput"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleTagKeyDown}
            onBlur={handleAddTag}
            placeholder="Add tag, press Enter"
            disabled={isSubmitting}
            className="flex-grow px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
        </div>
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="hover:text-blue-900"
                  aria-label={`Remove tag ${tag}`}
                >
                  &times;
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Recurrence */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <input
            type="checkbox"
            checked={isRecurring}
            onChange={(e) => {
              setIsRecurring(e.target.checked)
              if (!e.target.checked) setRecurrenceRule("")
            }}
            disabled={isSubmitting}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          Recurring task
        </label>
        {isRecurring && (
          <select
            value={recurrenceRule}
            onChange={(e) => setRecurrenceRule(e.target.value)}
            disabled={isSubmitting}
            className="mt-2 w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">Select frequency</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting || !title.trim()}
        className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors"
      >
        {isSubmitting ? (
          <span className="flex items-center justify-center">
            <svg
              className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Creating...
          </span>
        ) : (
          "Create Task"
        )}
      </button>
    </form>
  )
}
