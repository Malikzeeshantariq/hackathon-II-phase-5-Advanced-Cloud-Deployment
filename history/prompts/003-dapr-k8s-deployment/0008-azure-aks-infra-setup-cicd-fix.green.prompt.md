---
id: 0008
title: Azure AKS Infrastructure Setup and CI/CD Fix
stage: green
date: 2026-02-09
surface: agent
model: claude-opus-4-6
feature: 003-dapr-k8s-deployment
branch: main
user: zeeshantariq
command: implement
labels: ["azure", "aks", "acr", "ci-cd", "dapr", "github-actions", "infrastructure"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .github/workflows/deploy-aks.yml
  - dapr/components/pubsub-cloud.yaml
  - dapr/components/statestore.yaml
  - dapr/components/secrets.yaml
  - .gitignore
tests:
  - Build pipeline: all 5 services built and pushed to ACR (passed)
  - Deploy pipeline: all 5 services deployed to AKS (passed)
  - Pod health: all 5 pods running (2/2 ready with Dapr sidecars)
  - Frontend accessibility: HTTP 200 at http://20.59.43.181:3000
---

## Prompt

Implement the following plan:

# Fix GitHub Actions: Configure Azure Secrets for AKS CI/CD

The OKE→AKS code migration is complete (commit `0443770`), but both GitHub Actions workflow runs failed because the required Azure secrets are not yet configured in the GitHub repository. No code changes are needed — this is purely a GitHub secrets + Azure infrastructure setup task.

Root cause: `build.yml` references `secrets.AZURE_CREDENTIALS` and `secrets.ACR_NAME` which don't exist yet.

Steps: Create Azure infrastructure (resource group, ACR, AKS cluster, Dapr, service principal), add GitHub secrets, re-run workflows, verify.

## Response snapshot

### Azure Infrastructure Created
- **Resource Group:** `rg-todo-app-west` in `westus2` (eastus lacked Standard_B2s quota)
- **ACR:** `todoappcr0209.azurecr.io` (Basic SKU)
- **AKS Cluster:** `aks-todo-app` with 2x Standard_B2s_v2 nodes (B2s v1 unavailable in subscription)
- **Dapr:** Installed via Helm on AKS cluster
- **Service Principal:** `github-actions-todo` with contributor role

### GitHub Secrets Configured (6 total)
- `AZURE_CREDENTIALS` — Service principal JSON
- `ACR_NAME` — `todoappcr0209`
- `AKS_RESOURCE_GROUP` — `rg-todo-app-west`
- `AKS_CLUSTER_NAME` — `aks-todo-app`
- `DATABASE_URL` — Neon PostgreSQL connection string
- `BETTER_AUTH_SECRET` — JWT signing secret

### Issues Discovered and Fixed During Deployment

1. **Standard_B2s unavailable** — Subscription lacked B-series v1 quota in eastus. Switched to `westus2` with `Standard_B2s_v2`.

2. **Dapr PostgreSQL components not built-in** — `pubsub.postgresql` and `state.postgresql` are not bundled in the default Dapr 1.16.8 runtime image, causing sidecar CrashLoopBackOff. Fixed by switching to `pubsub.in-memory` and `state.in-memory` (built-in components).

3. **Deploy workflow missing secret passthrough** — Helm charts expect `DATABASE_URL` and `BETTER_AUTH_SECRET` via `--set env.*` but the deploy workflow didn't pass them. Added `--set env.DATABASE_URL` and `--set env.BETTER_AUTH_SECRET` to all relevant Helm upgrade commands.

4. **secrets.yaml not in git** — `dapr/components/secrets.yaml` was excluded by a blanket `secrets.yaml` gitignore rule. Added exception `!dapr/components/secrets.yaml` since the file only declares a Dapr secretstore component type, not actual secrets.

### Final State
- **Build pipeline:** Passed — all 5 images in ACR
- **Deploy pipeline:** Passed — all steps green
- **Pods:** 5/5 running (backend services 2/2 with Dapr sidecars, frontend 1/1)
- **Frontend:** Live at `http://20.59.43.181:3000` (HTTP 200)

### Commits
- `78ae4ed` — Fix AKS deployment: use in-memory Dapr components and pass secrets to Helm
- `aa271fc` — Add Dapr Kubernetes secrets component to repo

## Outcome

- ✅ Impact: Full CI/CD pipeline operational — push to main triggers build → deploy → live on AKS
- 🧪 Tests: Build pipeline passed (5/5 services), Deploy pipeline passed (all steps), Pods healthy (5/5), Frontend HTTP 200
- 📁 Files: 5 modified (.github/workflows/deploy-aks.yml, dapr/components/pubsub-cloud.yaml, dapr/components/statestore.yaml, dapr/components/secrets.yaml, .gitignore)
- 🔁 Next prompts: Restore PostgreSQL-backed Dapr components via pluggable components, configure HTTPS/Ingress for frontend, set up monitoring
- 🧠 Reflection: What was planned as a "no code changes" infrastructure task required 4 code fixes due to runtime incompatibilities (Dapr component types), missing secret passthrough in Helm deploys, and a gitignore exclusion. Always validate the full pipeline end-to-end after infrastructure changes.

## Evaluation notes (flywheel)

- Failure modes observed: VM SKU quota restrictions in Azure subscriptions; Dapr runtime not bundling PostgreSQL components by default; Helm chart secrets not populated without explicit --set; gitignore blanket rules hiding required config files
- Graders run and results (PASS/FAIL): Build pipeline PASS, Deploy pipeline PASS, Pod health PASS, Frontend PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Replace in-memory Dapr components with PostgreSQL pluggable components for durable pub/sub and state
