---
description: Implement JWT authentication with Better Auth for the Todo application. Handles security best practices, token validation, and HTTP authorization headers.
handoffs:
  - label: Create Auth Spec
    agent: sp.specify
    prompt: Create a specification for user authentication with JWT
  - label: Plan Auth Architecture
    agent: sp.plan
    prompt: Design the authentication architecture
  - label: Generate Auth Tasks
    agent: sp.tasks
    prompt: Generate implementation tasks for authentication
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are an authentication specialist implementing JWT-based authentication for the Todo application using Better Auth on the frontend.

### Requirements Summary

- **JWT Authentication**: Secure token-based authentication
- **Better Auth**: Frontend authentication library integration
- **Security Best Practices**: OWASP-compliant implementation
- **Token Validation**: Server-side token verification
- **HTTP Authorization Headers**: Bearer token handling

---

## Phase 1: Authentication Architecture Analysis

Before implementing, analyze the current project state:

1. **Check for existing auth code**:
   ```bash
   find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" \) | xargs grep -l -i "auth\|jwt\|token\|login\|session" 2>/dev/null || echo "No existing auth code found"
   ```

2. **Check for Better Auth installation**:
   ```bash
   cat package.json 2>/dev/null | grep -i "better-auth" || echo "Better Auth not installed"
   ```

3. **Check for environment configuration**:
   ```bash
   cat .env.example 2>/dev/null || cat .env.template 2>/dev/null || echo "No env template found"
   ```

---

## Phase 2: JWT Token Strategy

### Token Structure

Define the JWT payload structure (claims):

```typescript
interface JWTPayload {
  // Standard claims
  sub: string;          // Subject (user ID)
  iat: number;          // Issued at (Unix timestamp)
  exp: number;          // Expiration (Unix timestamp)
  iss: string;          // Issuer (your app identifier)
  aud: string;          // Audience (intended recipient)

  // Custom claims
  email: string;
  role: 'user' | 'admin';
  permissions?: string[];
}
```

### Token Lifecycle

| Token Type | Duration | Storage | Refresh Strategy |
|------------|----------|---------|------------------|
| Access Token | 15 minutes | Memory only | Silent refresh |
| Refresh Token | 7 days | HttpOnly cookie | Rotate on use |

### Security Requirements

- [ ] Access tokens: Short-lived (15 min max)
- [ ] Refresh tokens: HttpOnly, Secure, SameSite=Strict cookies
- [ ] Token rotation: New refresh token on each use
- [ ] Signature algorithm: RS256 or ES256 (asymmetric)
- [ ] Never store tokens in localStorage (XSS vulnerable)

---

## Phase 3: Better Auth Frontend Integration

### Installation

```bash
npm install better-auth
# or
pnpm add better-auth
```

### Configuration

Create the auth client configuration:

```typescript
// lib/auth-client.ts
import { createAuthClient } from "better-auth/client";

export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000",
  // Enable secure defaults
  credentials: "include", // Send cookies with requests
});

export const {
  signIn,
  signUp,
  signOut,
  useSession,
  getSession
} = authClient;
```

### Auth Provider Setup

```typescript
// providers/auth-provider.tsx
"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { authClient } from "@/lib/auth-client";

interface User {
  id: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check session on mount
    checkSession();
  }, []);

  async function checkSession() {
    try {
      const session = await authClient.getSession();
      setUser(session?.user ?? null);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  // ... implement signIn, signUp, signOut methods

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};
```

---

## Phase 4: Backend Token Validation

### HTTP Authorization Header Handling

```typescript
// middleware/auth.ts
import { verify, JwtPayload } from "jsonwebtoken";

interface AuthenticatedRequest extends Request {
  user?: JWTPayload;
}

export async function validateToken(req: AuthenticatedRequest): Promise<boolean> {
  // Extract token from Authorization header
  const authHeader = req.headers.get("Authorization");

  if (!authHeader?.startsWith("Bearer ")) {
    return false;
  }

  const token = authHeader.slice(7); // Remove "Bearer " prefix

  try {
    // Verify token signature and expiration
    const payload = verify(token, process.env.JWT_PUBLIC_KEY!, {
      algorithms: ["RS256"],
      issuer: process.env.JWT_ISSUER,
      audience: process.env.JWT_AUDIENCE,
    }) as JwtPayload;

    // Attach user to request
    req.user = payload;
    return true;
  } catch (error) {
    // Log but don't expose error details
    console.error("Token validation failed:", error.name);
    return false;
  }
}
```

### Token Validation Checklist

- [ ] Verify signature with public key
- [ ] Check `exp` claim (not expired)
- [ ] Check `iat` claim (not issued in future)
- [ ] Validate `iss` claim matches expected issuer
- [ ] Validate `aud` claim matches your application
- [ ] Check token hasn't been revoked (if using blocklist)

---

## Phase 5: Security Best Practices

### OWASP Authentication Recommendations

| Practice | Implementation |
|----------|----------------|
| Secure password storage | bcrypt/argon2 with cost factor >= 12 |
| Brute force protection | Rate limiting + account lockout |
| Session fixation | Generate new session ID on login |
| Credential stuffing | CAPTCHA + breach database check |
| HTTPS only | Strict-Transport-Security header |
| CSRF protection | SameSite cookies + CSRF tokens |

### Environment Variables (Never Hardcode!)

```bash
# .env.example
# JWT Configuration
JWT_SECRET_KEY=           # For symmetric (HS256) - NOT RECOMMENDED
JWT_PRIVATE_KEY=          # For asymmetric (RS256) - RECOMMENDED
JWT_PUBLIC_KEY=           # For asymmetric verification
JWT_ISSUER=todo-app
JWT_AUDIENCE=todo-app-users
JWT_ACCESS_TOKEN_EXPIRY=15m
JWT_REFRESH_TOKEN_EXPIRY=7d

# Better Auth
BETTER_AUTH_SECRET=       # Generate with: openssl rand -base64 32
BETTER_AUTH_URL=http://localhost:3000

# Database (for session storage)
DATABASE_URL=
```

### Security Headers

```typescript
// middleware/security-headers.ts
export const securityHeaders = {
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "X-XSS-Protection": "1; mode=block",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'",
};
```

---

## Phase 6: Implementation Tasks

Generate the following tasks when implementing:

### Backend Tasks
1. [ ] Set up JWT key pair generation (RS256)
2. [ ] Create token generation service
3. [ ] Implement token validation middleware
4. [ ] Create refresh token rotation logic
5. [ ] Add token revocation (logout/blocklist)
6. [ ] Set up rate limiting for auth endpoints

### Frontend Tasks
1. [ ] Install and configure Better Auth client
2. [ ] Create AuthProvider context
3. [ ] Implement sign-in form with validation
4. [ ] Implement sign-up form with validation
5. [ ] Add protected route wrapper
6. [ ] Handle token refresh silently
7. [ ] Implement sign-out with token cleanup

### Security Tasks
1. [ ] Configure CORS for auth endpoints
2. [ ] Set up HTTPS in production
3. [ ] Implement CSRF protection
4. [ ] Add security headers middleware
5. [ ] Set up audit logging for auth events
6. [ ] Configure secure cookie settings

---

## Validation Checklist

Before completing auth implementation, verify:

### Token Security
- [ ] Tokens are signed with asymmetric keys (RS256/ES256)
- [ ] Access tokens expire within 15 minutes
- [ ] Refresh tokens are HttpOnly cookies
- [ ] Tokens are never stored in localStorage
- [ ] Token rotation is implemented

### API Security
- [ ] All auth endpoints use HTTPS
- [ ] Rate limiting is configured
- [ ] CORS is properly restricted
- [ ] Input validation on all auth inputs
- [ ] Error messages don't leak information

### Frontend Security
- [ ] No sensitive data in client-side storage
- [ ] XSS protections in place
- [ ] CSRF tokens for state-changing requests
- [ ] Secure password requirements enforced

---

## Quick Reference

### Common Auth Flows

**Login Flow:**
```
1. User submits credentials
2. Server validates credentials
3. Server generates access + refresh tokens
4. Access token returned in response body
5. Refresh token set as HttpOnly cookie
6. Client stores access token in memory
```

**Token Refresh Flow:**
```
1. Access token expires (or about to)
2. Client calls /auth/refresh
3. Server validates refresh token from cookie
4. Server rotates refresh token
5. New access token returned
6. Client updates in-memory token
```

**Logout Flow:**
```
1. Client calls /auth/logout
2. Server adds refresh token to blocklist
3. Server clears refresh token cookie
4. Client clears in-memory access token
5. Client redirects to login
```

---

As the main request completes, you MUST create and complete a PHR (Prompt History Record) using agent-native tools when possible.

1) Determine Stage
   - Stage: constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general

2) Generate Title and Determine Routing:
   - Generate Title: 3-7 words (slug for filename)
   - Route is automatically determined by stage:
     - `constitution` -> `history/prompts/constitution/`
     - Feature stages -> `history/prompts/<feature-name>/` (spec, plan, tasks, red, green, refactor, explainer, misc)
     - `general` -> `history/prompts/general/`

3) Create and Fill PHR (Shell first; fallback agent-native)
   - Run: `.specify/scripts/bash/create-phr.sh --title "<title>" --stage <stage> [--feature <name>] --json`
   - Open the file and fill remaining placeholders (YAML + body), embedding full PROMPT_TEXT (verbatim) and concise RESPONSE_TEXT.
   - If the script fails:
     - Read `.specify/templates/phr-template.prompt.md` (or `templates/...`)
     - Allocate an ID; compute the output path based on stage from step 2; write the file
     - Fill placeholders and embed full PROMPT_TEXT and concise RESPONSE_TEXT

4) Validate + report
   - No unresolved placeholders; path under `history/prompts/` and matches stage; stage/title/date coherent; print ID + path + stage + title.
   - On failure: warn, don't block. Skip only for `/sp.phr`.
