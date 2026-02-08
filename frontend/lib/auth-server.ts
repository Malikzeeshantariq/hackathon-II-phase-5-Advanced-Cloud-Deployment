/**
 * Better Auth server configuration.
 *
 * Spec Reference: plan.md - Authentication Architecture
 * This runs on the Next.js server and handles:
 * - User registration and login
 * - Session management
 */

import { betterAuth } from "better-auth"
import { jwt } from "better-auth/plugins"
import { Pool } from "pg"

/**
 * Get the base URL for the application.
 * Works in both development and production (Vercel).
 */
function getBaseUrl(): string {
  // Check for explicit app URL first
  if (process.env.NEXT_PUBLIC_APP_URL) {
    return process.env.NEXT_PUBLIC_APP_URL
  }
  // Vercel deployment URL (automatically set by Vercel)
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`
  }
  // Fallback for local development
  return "http://localhost:3000"
}

const baseUrl = getBaseUrl()

/**
 * Better Auth server instance.
 *
 * Configured to use:
 * - Email + password authentication
 * - JWT plugin for generating tokens for FastAPI backend
 * - PostgreSQL database (Neon) for user storage
 */
export const auth = betterAuth({
  // Use the shared secret for JWT signing
  secret: process.env.BETTER_AUTH_SECRET,

  // PostgreSQL database connection (same as backend)
  database: new Pool({
    connectionString: process.env.DATABASE_URL,
  }),

  // Email + password authentication
  emailAndPassword: {
    enabled: true,
    // Minimum password length
    minPasswordLength: 8,
  },

  // Plugins
  plugins: [
    // JWT plugin for generating tokens that FastAPI can verify
    jwt({
      jwt: {
        // Token expires in 7 days
        expirationTime: "7d",
        // Use issuer and audience for verification
        issuer: baseUrl,
        audience: baseUrl,
      },
    }),
  ],

  // Trust the host header for URL detection
  // ADDITIONAL_TRUSTED_ORIGINS env var allows adding origins for K8s deployment
  trustedOrigins: [
    "http://localhost:3000",
    "https://todo-app2pk.vercel.app",
    // Add any additional origins from environment variable (comma-separated)
    ...(process.env.ADDITIONAL_TRUSTED_ORIGINS?.split(",").filter(Boolean) || []),
  ],
})

export type Session = typeof auth.$Infer.Session
export type User = typeof auth.$Infer.Session.user
