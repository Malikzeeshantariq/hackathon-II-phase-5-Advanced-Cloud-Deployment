"use client"

/**
 * Sign out button with redirect to home page.
 */

import { authClient, clearAuthToken } from "@/lib/auth"

export default function SignOutButton() {
  const handleSignOut = async () => {
    console.log("Sign out clicked")

    try {
      // Clear cached JWT token
      clearAuthToken()

      // Sign out from Better Auth
      await authClient.signOut()

      console.log("Sign out successful, redirecting...")

      // Redirect to home page
      window.location.href = "/"
    } catch (error) {
      console.error("Sign out error:", error)
      // Still redirect even if there's an error
      window.location.href = "/"
    }
  }

  return (
    <button
      onClick={handleSignOut}
      type="button"
      className="text-sm text-gray-600 hover:text-gray-900 transition-colors cursor-pointer"
    >
      Sign Out
    </button>
  )
}
