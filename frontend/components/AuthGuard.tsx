/**
 * T017: AuthGuard component for route protection.
 *
 * Spec Reference: AR-001 - Protected routes require JWT
 */

"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useSession } from "@/lib/auth"

interface AuthGuardProps {
  children: React.ReactNode
}

/**
 * Protects routes that require authentication.
 *
 * Redirects unauthenticated users to the login page.
 * Shows a loading state while checking authentication.
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter()
  const { data: session, isPending } = useSession()
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    if (!isPending) {
      if (!session?.user) {
        // Not authenticated - redirect to login
        router.push("/login")
      } else {
        setIsChecking(false)
      }
    }
  }, [session, isPending, router])

  // Show loading while checking authentication
  if (isPending || isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // User is authenticated - render children
  return <>{children}</>
}
