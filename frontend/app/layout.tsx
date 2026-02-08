/**
 * T016: Root layout with auth provider.
 *
 * Spec Reference: plan.md - Frontend Components
 */

import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Todo App",
  description: "Task management application with JWT authentication",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        {children}
      </body>
    </html>
  )
}
