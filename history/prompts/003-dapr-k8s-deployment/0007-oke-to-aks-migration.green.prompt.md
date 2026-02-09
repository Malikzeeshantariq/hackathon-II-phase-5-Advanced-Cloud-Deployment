---
id: 0007
title: OKE to AKS Migration
stage: green
date: 2026-02-09
surface: agent
model: claude-opus-4-6
feature: 003-dapr-k8s-deployment
branch: main
user: zeeshantariq
command: implement
labels: ["migration", "azure", "aks", "acr", "ci-cd"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .github/workflows/build.yml
  - .github/workflows/deploy-aks.yml
  - scripts/deploy-cloud.sh
  - charts/todo-backend/values-cloud.yaml
  - charts/todo-frontend/values-cloud.yaml
  - charts/notification-service/values-cloud.yaml
  - charts/recurring-service/values-cloud.yaml
  - charts/audit-service/values-cloud.yaml
tests:
  - grep verification: no OCI/OCIR/OKE references remain in modified files
  - grep verification: Azure/ACR/AKS references correctly present
---

## Prompt

Implement the following plan:

# Migration Plan: Oracle OKE to Azure AKS

Context: This project (Part C) was built targeting Oracle Kubernetes Engine (OKE) Free Tier with Oracle Container Image Registry (OCIR). Migrate the cloud deployment to Azure Kubernetes Service (AKS) with Azure Container Registry (ACR). The application itself (5 Dapr-enabled services, Neon PostgreSQL, Helm charts, Dockerfiles) is cloud-agnostic -- only the CI/CD pipelines, cloud value files, and deployment scripts contain Oracle-specific references.

What stays the same: All application code, Dockerfiles, Helm templates, Dapr components, local Minikube setup, Neon PostgreSQL database.

What changes: 8 files total -- 2 GitHub Actions workflows, 5 Helm values-cloud.yaml files, 1 deploy script.

## Response snapshot

Migrated 8 files from Oracle OKE/OCIR to Azure AKS/ACR:

1. **`.github/workflows/build.yml`** — Replaced `oracle-actions/login-ocir@v1.2` with `azure/login@v2` + `az acr login`. Removed `NAMESPACE` env var. Changed registry to `ACR_NAME.azurecr.io`. Simplified image tags (flat ACR structure).

2. **`.github/workflows/deploy-aks.yml`** (renamed from `deploy-oke.yml`) — Replaced `oracle-actions/configure-kubectl-oke@v1` (6 OCI params) with `azure/login@v2` + `azure/aks-set-context@v4` (2 params: resource-group, cluster-name). Removed NAMESPACE from all `--set image.repository=` lines.

3. **`scripts/deploy-cloud.sh`** — Updated env var validation from `OCI_REGION OCIR_NAMESPACE` to `ACR_NAME`. Registry URL from `OCI_REGION.ocir.io/OCIR_NAMESPACE` to `ACR_NAME.azurecr.io`. Updated comments and error messages.

4. **5x `charts/*/values-cloud.yaml`** — Changed image repository from `${OCI_REGION}.ocir.io/${OCIR_NAMESPACE}/<service>` to `${ACR_NAME}.azurecr.io/<service>`. Updated comments. Resource limits, Dapr config unchanged.

Verified: zero remaining OCI/OCIR/OKE references in modified files.

## Outcome

- ✅ Impact: Complete cloud provider migration from Oracle OKE to Azure AKS across CI/CD and deployment configs
- 🧪 Tests: grep verification — no stale OCI references, all Azure references correct
- 📁 Files: 8 files modified (1 renamed, 1 deleted, 6 edited)
- 🔁 Next prompts: Configure Azure GitHub secrets, run build workflow, deploy to AKS
- 🧠 Reflection: Clean migration — app code is cloud-agnostic, only CI/CD plumbing needed changes. ACR flat namespace simplifies image paths vs OCIR's region/namespace/image structure.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): grep verification PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
