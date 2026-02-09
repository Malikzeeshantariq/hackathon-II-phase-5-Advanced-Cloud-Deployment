// Next.js configuration
import type { NextConfig } from 'next'

const BACKEND_URL = process.env.BACKEND_URL || 'http://todo-backend:8000'

const nextConfig: NextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,
  // T4-03: Enable standalone output for Docker deployment
  // Spec Reference: spec.md FR-1.2, plan.md Section 4.2
  output: 'standalone',
  // Ensure packages are transpiled correctly
  transpilePackages: ['better-auth'],
  serverExternalPackages: ['pg'],
  // Proxy API calls to the backend (so browser doesn't need direct backend access)
  async rewrites() {
    return [
      {
        // Proxy /api/:userId/tasks/* and /api/:userId/chat/* to backend
        // but NOT /api/auth/* (handled by Better Auth locally)
        source: '/api/:path((?!auth).*)',
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
