# T4-03: Frontend Dockerfile
# Spec Reference: spec.md FR-1.2, FR-1.3, FR-1.6
# Plan Reference: plan.md Section 4.2, 1.3

# ============================================
# Stage 1: Dependencies - Install npm packages
# ============================================
FROM node:20-alpine AS deps

WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json* ./

# Install all dependencies (including devDependencies for build)
RUN npm ci

# ============================================
# Stage 2: Build - Build Next.js application
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy all source files
COPY . .

# Build-time environment variables
# NEXT_PUBLIC_* variables are baked into the client bundle
ARG NEXT_PUBLIC_API_URL=http://todo-backend:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application (standalone mode configured in next.config.ts)
RUN npm run build

# ============================================
# Stage 3: Runtime - Minimal production image
# ============================================
FROM node:20-alpine AS runner

WORKDIR /app

# Set production environment
ENV NODE_ENV=production

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy public assets (if exists)
# Create empty public directory if it doesn't exist in the build
RUN mkdir -p ./public

# Copy standalone build output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose Next.js port
EXPOSE 3000

# Set port environment variable
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start the application
CMD ["node", "server.js"]
