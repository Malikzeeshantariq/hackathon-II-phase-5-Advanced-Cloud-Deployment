# Todo Full-Stack Web Application — Phase 5: Advanced Cloud Deployment

A multi-user task management application with AI chatbot, event-driven microservices, and automated cloud deployment on Azure AKS.

**Live:** `http://20.59.43.181:3000`

## Architecture

```
                         ┌──────────────────────────────────┐
                         │         Azure AKS Cluster         │
  ┌──────────┐           │                                    │
  │ Browser  │──────────▶│  ┌─────────────┐  ┌────────────┐  │
  └──────────┘    :3000  │  │  Frontend    │─▶│  Backend    │  │
                         │  │  (Next.js)   │  │  (FastAPI)  │  │
                         │  └─────────────┘  └─────┬──────┘  │
                         │                         │ Dapr     │
                         │         ┌───────────────┼────┐     │
                         │         ▼               ▼    ▼     │
                         │  ┌───────────┐ ┌──────┐ ┌──────┐  │
                         │  │Notification│ │Audit │ │Recur.│  │
                         │  │ Service    │ │Svc   │ │Svc   │  │
                         │  └───────────┘ └──────┘ └──────┘  │
                         └──────────────────────────────────┘
                                          │
                                          ▼
                                ┌──────────────────┐
                                │ Neon PostgreSQL   │
                                │ (Serverless)      │
                                └──────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS |
| Backend | Python 3.11, FastAPI, SQLModel |
| Database | Neon Serverless PostgreSQL |
| Auth | Better Auth (JWT tokens) |
| AI | OpenAI Agents SDK, MCP Tools |
| Events | Dapr Pub/Sub |
| Microservices | Notification, Audit, Recurring (Python/FastAPI + Dapr) |
| Container Registry | Azure ACR |
| Orchestration | Azure AKS (Kubernetes), Helm 3 |
| CI/CD | GitHub Actions |

## Features

- **Task Management** — CRUD with priorities, tags, due dates, filtering, sorting, and search
- **User Authentication** — Better Auth with JWT tokens, per-user data isolation
- **AI Chatbot** — Natural language task management via OpenAI Agents SDK with MCP tools
- **Reminders** — Recurring task scheduling and notifications
- **Event-Driven** — Dapr Pub/Sub for audit logging, notifications, and recurring task generation
- **Cloud Deployment** — Automated CI/CD to Azure AKS with Helm charts

## Project Structure

```
├── frontend/                 # Next.js 16 App Router
│   ├── app/                  # Pages (auth, dashboard, chat)
│   ├── components/           # React components
│   └── lib/                  # Auth client, API client, types
│
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── routers/          # Tasks, Reminders, Chat, Audit, Internal
│   │   ├── services/         # ChatService, AgentService, EventPublisher
│   │   ├── models/           # SQLModel schemas
│   │   ├── middleware/       # JWT verification
│   │   ├── mcp/              # MCP tool definitions
│   │   └── database.py       # Neon PostgreSQL connection
│   └── requirements.txt
│
├── services/                 # Dapr microservices
│   ├── audit/                # Audit logging (pub/sub consumer)
│   ├── notification/         # Task notifications (pub/sub consumer)
│   └── recurring/            # Recurring task generation (pub/sub consumer)
│
├── charts/                   # Helm charts (5 services)
│   ├── todo-backend/
│   ├── todo-frontend/
│   ├── audit-service/
│   ├── notification-service/
│   └── recurring-service/
│
├── dapr/                     # Dapr component definitions
│   └── components/           # Pub/Sub, State Store, Secrets
│
├── .github/workflows/        # CI/CD pipelines
│   ├── build.yml             # Build & push images to ACR
│   └── deploy-aks.yml        # Deploy to AKS with Helm
│
├── specs/                    # Spec-Driven Development artifacts
└── history/                  # Prompt History Records & ADRs
```

## API Endpoints

All endpoints require `Authorization: Bearer <token>` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/{user_id}/tasks` | List tasks (filter/sort/search) |
| POST | `/api/{user_id}/tasks` | Create task |
| GET | `/api/{user_id}/tasks/{id}` | Get task details |
| PUT | `/api/{user_id}/tasks/{id}` | Update task |
| DELETE | `/api/{user_id}/tasks/{id}` | Delete task |
| PATCH | `/api/{user_id}/tasks/{id}/complete` | Toggle completion |
| POST | `/api/{user_id}/chat` | AI chatbot message |
| GET | `/api/{user_id}/tasks/{id}/reminders` | List reminders |
| POST | `/api/{user_id}/tasks/{id}/reminders` | Create reminder |

## Local Development

### Prerequisites

- Node.js 20+, Python 3.11+, Docker
- Neon PostgreSQL database ([neon.tech](https://neon.tech))

### Setup

```bash
# Clone
git clone https://github.com/Malikzeeshantariq/hackathon-II-phase-5-Advanced-Cloud-Deployment.git
cd hackathon-II-phase-5-Advanced-Cloud-Deployment

# Environment
cp .env.example .env
# Edit .env with your DATABASE_URL, BETTER_AUTH_SECRET, OPENAI_API_KEY

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`

## Cloud Deployment (Azure AKS)

### Infrastructure

| Resource | Details |
|----------|---------|
| Resource Group | `rg-todo-app-west` (westus2) |
| Container Registry | `todoappcr0209.azurecr.io` |
| AKS Cluster | `aks-todo-app` (2x Standard_B2s_v2) |
| Dapr Runtime | Installed via Helm |

### CI/CD Pipeline

Push to `main` triggers the full pipeline:

1. **Build** — Builds multi-arch Docker images for all 5 services, pushes to ACR
2. **Deploy** — Applies Dapr components, creates K8s secrets, deploys via Helm, verifies rollout

### Manual Deployment

```bash
# Get cluster credentials
az aks get-credentials --resource-group rg-todo-app-west --name aks-todo-app

# Verify
kubectl get pods          # 5 services running
kubectl get svc           # Frontend LoadBalancer with external IP
```

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase II | Todo CRUD API with JWT auth (FastAPI + Next.js + Neon) | Complete |
| Phase III | AI Chatbot (OpenAI Agents SDK + MCP Tools) | Complete |
| Phase IV | Kubernetes deployment (Docker + Helm + Minikube) | Complete |
| Phase V-A | Advanced features + Dapr event-driven microservices | Complete |
| Phase V-B | Multi-service K8s deployment with Dapr sidecars | Complete |
| Phase V-C | Cloud deployment (Azure AKS + ACR + GitHub Actions CI/CD) | Complete |

## Cost Estimate (Azure)

| Resource | Monthly Cost |
|----------|-------------|
| 2x Standard_B2s_v2 nodes | ~$60 |
| ACR Basic | ~$5 |
| Standard Load Balancer | ~$22 |
| **Total** | **~$87/month** |

AKS control plane is free tier. Neon PostgreSQL free tier is separate.
