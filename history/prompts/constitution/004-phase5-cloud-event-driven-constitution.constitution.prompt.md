---
id: 004
title: Phase 5 Cloud Event-Driven Constitution
stage: constitution
date: 2026-02-08
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: zeeshantariq
command: /sp.constitution
labels: ["constitution", "phase5", "dapr", "event-driven", "oracle-oke", "kafka", "ci-cd", "governance"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (governance document, no executable tests)
---

## Prompt

Create or update the file `sp.constitution` for the Todo AI Chatbot project.

Context:
- The project follows Spec-Driven, AI-Native, Cloud-Native Software Development.
- Phase 2: Full-stack app (Next.js + FastAPI + SQLModel + Neon).
- Phase 3: AI system with OpenAI Agents SDK, MCP tools, ChatKit UI, stateless AI, PostgreSQL memory.
- Phase 4: Containerization and local Kubernetes with Docker, Minikube, Helm, kubectl-ai, kagent, Gordon.
- Phase 5: Advanced cloud-native, event-driven architecture with:
  - Oracle Cloud (OKE) as primary cloud target (Always Free tier)
  - Kubernetes (OKE)
  - Dapr (Pub/Sub, State, Jobs, Secrets, Service Invocation)
  - Kafka / Redpanda (managed or in-cluster)
  - Multiple services: Chat API, Notification, Recurring Task, Audit, WebSocket Sync
  - CI/CD with GitHub Actions
  - Observability (logging, metrics, monitoring)
- Phase 2, 3, and 4 artifacts are immutable and treated as stable contracts.
- Infrastructure and operations must be spec-governed (no manual ops).

Requirements for sp.constitution:
1. Must define non-negotiable principles for spec-first development, tool-mediated AI behavior (MCP), event-driven architecture, stateless services + persistent state (DB/State store), deterministic auditable infrastructure, cloud reproducibility (Oracle OKE).
2. Must include sections: SYNC IMPACT REPORT, Project, Core Principles, Key Standards, Technical Constraints, Architecture Constraints, AI & MCP Governance Rules, Infrastructure Governance Rules, Event-Driven Governance Rules, Quality/Security/Validation Rules, Success Criteria (Phase 5), Failure Conditions, Enforcement, Governance.
3. Must explicitly state: AI agents may only act via MCP tools, MCP tools are stateless and deterministic, all side effects go through tools or Dapr, no manual operations outside specs, docker-fastapi and kubernetes skills remain approved, CI/CD is mandatory, Oracle OKE is primary cloud target.
4. Must include clear versioning (bump MAJOR for Phase 5), dates, audit-friendly language.
5. Tone: Formal, normative language (MUST/MUST NOT/SHOULD/MAY per RFC 2119), enforceable governance-style document.

## Response snapshot

Updated `.specify/memory/constitution.md` from version 3.0.0 to 4.0.0 (MAJOR bump). The constitution now governs Phase V of the Todo AI System with comprehensive additions:

**Version Change**: 3.0.0 → 4.0.0

**Key Changes**:
- Extended all four Core Principles to cover Dapr, event-driven architecture, and cloud governance
- Added Dapr Governance Rules (Pub/Sub, State, Jobs, Secrets, Service Invocation via sidecar model)
- Added Event-Driven (Kafka/Redpanda) Governance Rules (topic versioning, schema backward-compatibility, idempotent consumers, dead-letter handling)
- Added Infrastructure & Cloud Governance Rules (Oracle OKE as primary cloud target, Helm-only deployments)
- Added CI/CD & Observability Rules (GitHub Actions mandatory, health endpoints, structured logging)
- Expanded Technical Constraints with multi-service architecture, Dapr, Kafka, Oracle OKE, CI/CD, observability
- Marked Phase III and Phase IV Success Criteria as complete
- Added comprehensive Phase V Success Criteria
- Added Compliance Review subsection under Governance

**Oracle OKE** designated as primary cloud target (Always Free tier). All cloud specs MUST target OKE first.

## Outcome

- Impact: MAJOR governance update — Phase V constitution ratified with event-driven, multi-service, cloud-native, and CI/CD governance
- Tests: N/A (governance document)
- Files: `.specify/memory/constitution.md` (updated)
- Next prompts: Create sp5.spec.md, sp5.plan.md, sp5.tasks.md; update spec/plan/tasks templates for Dapr + Event-Driven + Cloud checks
- Reflection: Constitution successfully extended from Phase IV single-cluster model to Phase V multi-service, event-driven, cloud-deployed architecture with Dapr as the distributed runtime abstraction layer

## Evaluation notes (flywheel)

- Failure modes observed: None — user provided comprehensive input that aligned with template structure
- Graders run and results (PASS/FAIL): Manual validation PASS — no unresolved placeholders, version matches report, dates in ISO format, all RFC 2119 language applied
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate template propagation by running /sp.plan against the new constitution version
