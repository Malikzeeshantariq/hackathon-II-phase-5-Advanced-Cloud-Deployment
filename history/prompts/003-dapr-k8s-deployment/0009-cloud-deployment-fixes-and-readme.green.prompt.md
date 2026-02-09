---
id: 0009
title: Cloud Deployment Fixes and README Update
stage: green
date: 2026-02-09
surface: agent
model: claude-opus-4-6
feature: 003-dapr-k8s-deployment
branch: main
user: zeeshantariq
command: implement
labels: ["azure", "aks", "auth", "proxy", "openai", "readme", "ci-cd", "trusted-origins"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .github/workflows/deploy-aks.yml
  - frontend/next.config.ts
  - frontend/lib/api-client.ts
  - frontend/lib/chat-client.ts
  - README.md
tests:
  - Build pipeline: all 5 services built and pushed to ACR (passed x3 runs)
  - Deploy pipeline: all steps green including new frontend IP detection (passed)
  - Auth login: working at http://20.59.43.181:3000 after trusted origins fix
  - Dashboard tasks: loading successfully after Next.js rewrite proxy fix
  - OpenAI chatbot: working after OPENAI_API_KEY added to backend
  - Pod health: all 5 pods running (2/2 Dapr sidecars)
---

## Prompt

After successful AKS deployment (PHR 0008), three runtime issues were discovered and fixed:

1. Login returned "invalid email/password" — Better Auth rejected requests from untrusted origin (external IP)
2. Dashboard showed "Error loading tasks" — browser couldn't resolve K8s internal DNS `todo-backend:8000`
3. AI chatbot returned "error processing request" — OPENAI_API_KEY not set in backend pod

Additionally, the README was completely outdated (contained kubectl-ai docs from Google, unrelated to this project).

## Response snapshot

### Fix 1: Better Auth Trusted Origins (commit `0de3d56`)

Better Auth rejects login/signup from origins not in its `trustedOrigins` list. The external IP `http://20.59.43.181:3000` was not listed.

**Solution:** Set `ADDITIONAL_TRUSTED_ORIGINS` env var on the frontend pod via Helm `--set`. Updated `deploy-aks.yml` to auto-detect the frontend LoadBalancer IP and pass it as a trusted origin.

### Fix 2: API Proxy via Next.js Rewrites (commit `a81b2f1`)

`NEXT_PUBLIC_API_URL` was baked into the Docker image at build time as `http://todo-backend:8000`. Server-side rendering could resolve this K8s DNS name, but client-side (browser) API calls failed because the browser cannot resolve Kubernetes service names.

**Solution:**
- Added Next.js `rewrites` in `next.config.ts` to proxy `/api/*` (except `/api/auth/*`) through the frontend server to `http://todo-backend:8000`
- Updated `api-client.ts` and `chat-client.ts` to use relative URLs in production so all browser API calls go through the same-origin proxy
- No backend changes needed — the proxy is transparent

### Fix 3: OpenAI API Key (commit `1cf93b6`)

The backend Helm chart supports `OPENAI_API_KEY` via `env.OPENAI_API_KEY` but the deploy workflow wasn't passing it.

**Solution:** Added `OPENAI_API_KEY` as a GitHub secret and added `--set env.OPENAI_API_KEY` to the backend deploy step in `deploy-aks.yml`.

### Fix 4: README Replacement (commit `4d0b565`)

The README contained the entire kubectl-ai documentation from Google (475 lines), completely unrelated to this project.

**Solution:** Replaced with comprehensive Phase 5 project documentation covering architecture diagram, tech stack, features, project structure, API endpoints, local development setup, Azure AKS cloud deployment, CI/CD pipeline, development phases, and cost estimates.

### Commits
- `0de3d56` — Add trusted origins and frontend IP detection to deploy workflow
- `a81b2f1` — Proxy API calls through Next.js rewrites for cloud deployment
- `1cf93b6` — Pass OPENAI_API_KEY to backend in deploy workflow
- `4d0b565` — Replace placeholder README with Phase 5 project documentation

## Outcome

- ✅ Impact: All app functionality working end-to-end on AKS — auth, tasks CRUD, AI chatbot. README accurately documents the project.
- 🧪 Tests: Auth login PASS, Dashboard tasks PASS, AI chatbot PASS, Build pipeline PASS (3 runs), Deploy pipeline PASS (all steps green)
- 📁 Files: 5 modified (deploy-aks.yml, next.config.ts, api-client.ts, chat-client.ts, README.md)
- 🔁 Next prompts: Configure HTTPS/TLS ingress, set up custom domain, add monitoring/alerting
- 🧠 Reflection: Cloud deployments surface issues invisible in local dev — browser vs server-side URL resolution, origin trust policies, and missing secrets. Each required a different fix pattern: env var passthrough, architectural proxy, and CI/CD pipeline update. The initial "no code changes needed" assessment from the plan was overly optimistic; real deployments always have runtime surprises.

## Evaluation notes (flywheel)

- Failure modes observed: NEXT_PUBLIC_* vars baked at build time can't change per environment; Better Auth origin validation blocks external IPs by default; Helm chart secrets need explicit --set passthrough in CI/CD; placeholder READMEs from template repos persist unnoticed
- Graders run and results (PASS/FAIL): Auth PASS, Tasks API PASS, Chatbot PASS, Build CI PASS, Deploy CD PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Use Next.js runtime env vars instead of build-time NEXT_PUBLIC_* to avoid rebuild-per-environment issue
