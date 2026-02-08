// Next.js configuration
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,
  // T4-03: Enable standalone output for Docker deployment
  // Spec Reference: spec.md FR-1.2, plan.md Section 4.2
  output: 'standalone',
  // Ensure packages are transpiled correctly
  transpilePackages: ['better-auth'],
  serverExternalPackages: ['pg'],
}

export default nextConfig
