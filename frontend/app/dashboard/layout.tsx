/**
 * T026: Protected dashboard layout.
 *
 * Spec Reference: AR-001 - Protected routes require authentication
 */
"use client";

import { createContext, useContext, useState, useCallback } from "react";
import AuthGuard from "@/components/AuthGuard";
import SignOutButton from "@/components/SignOutButton";
import FloatingChat from "@/components/FloatingChat";

// Context for task refresh
interface TaskRefreshContextType {
  refreshKey: number;
  triggerRefresh: () => void;
}

export const TaskRefreshContext = createContext<TaskRefreshContextType>({
  refreshKey: 0,
  triggerRefresh: () => {},
});

export const useTaskRefresh = () => useContext(TaskRefreshContext);

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [refreshKey, setRefreshKey] = useState(0);

  const triggerRefresh = useCallback(() => {
    setRefreshKey((prev) => prev + 1);
  }, []);

  return (
    <AuthGuard>
      <TaskRefreshContext.Provider value={{ refreshKey, triggerRefresh }}>
        <div className="min-h-screen bg-gray-50">
          {/* Navigation header */}
          <header className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-8">
                <h1 className="text-xl font-semibold text-gray-900">Todo App</h1>
              </div>
              <nav>
                <SignOutButton />
              </nav>
            </div>
          </header>

          {/* Main content */}
          <main className="max-w-4xl mx-auto px-4 py-8">{children}</main>

          {/* Floating AI Chat */}
          <FloatingChat onTaskUpdate={triggerRefresh} />
        </div>
      </TaskRefreshContext.Provider>
    </AuthGuard>
  );
}
