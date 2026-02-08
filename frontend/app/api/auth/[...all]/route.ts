/**
 * Better Auth API route handler.
 *
 * This catch-all route handles all /api/auth/* requests including:
 * - /api/auth/signin
 * - /api/auth/signup
 * - /api/auth/signout
 * - /api/auth/session
 * - /api/auth/token
 * - /api/auth/jwks
 */

import { auth } from "@/lib/auth-server"
import { toNextJsHandler } from "better-auth/next-js"

export const { GET, POST } = toNextJsHandler(auth)
