/**
 * T013: Better Auth client configuration.
 *
 * Spec Reference: plan.md - Authentication Architecture
 * Spec Reference: research.md - Authentication: Better Auth with JWT
 */

import { createAuthClient } from "better-auth/react"
import { jwtClient } from "better-auth/client/plugins"

/**
 * Better Auth client instance.
 *
 * Handles:
 * - User signup and signin
 * - JWT token management via jwt plugin
 * - Session state
 *
 * Note: baseURL points to Next.js server (same origin) for auth,
 * NOT the FastAPI backend. The JWT token is then used for FastAPI calls.
 */
export const authClient = createAuthClient({
  // Auth is handled by Next.js /api/auth routes (same origin)
  // Leave empty or use relative path for same-origin requests
  baseURL: typeof window !== "undefined" ? window.location.origin : "",
  plugins: [
    // JWT plugin for generating tokens for API calls
    jwtClient(),
  ],
})

// Store the JWT token in memory for API calls
let cachedToken: string | null = null
let tokenExpiry: number | null = null

/**
 * Get the current session's JWT token for API calls.
 *
 * Uses the jwt plugin to get a token that can be
 * verified by the FastAPI backend using the shared secret.
 *
 * @returns JWT token string or null if not authenticated
 */
export async function getAuthToken(): Promise<string | null> {
  // Check if we have a valid cached token
  if (cachedToken && tokenExpiry && Date.now() < tokenExpiry) {
    return cachedToken
  }

  try {
    // Get JWT token from the server via /api/auth/token endpoint
    const result = await authClient.token()
    if (result.data?.token) {
      cachedToken = result.data.token
      // Cache for 6 days (token expires in 7 days)
      tokenExpiry = Date.now() + 6 * 24 * 60 * 60 * 1000
      return cachedToken
    }
  } catch (error) {
    console.error("Failed to get JWT token:", error)
  }

  return null
}

/**
 * Clear the cached token (call on logout).
 */
export function clearAuthToken(): void {
  cachedToken = null
  tokenExpiry = null
}

/**
 * Check if user is authenticated.
 *
 * @returns true if user has a valid session
 */
export async function isAuthenticated(): Promise<boolean> {
  const session = await authClient.getSession()
  return !!session.data?.user
}

/**
 * Get current user information.
 *
 * @returns User object or null if not authenticated
 */
export async function getCurrentUser() {
  const session = await authClient.getSession()
  return session.data?.user || null
}

// Re-export commonly used auth functions
export const { signIn, signUp, signOut, useSession } = authClient
