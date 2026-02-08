# Quickstart: Todo CRUD API

**Feature**: 001-todo-crud-api
**Date**: 2025-01-08

## Prerequisites

- Python 3.11+
- Node.js 18+ (LTS)
- Git
- Neon PostgreSQL account (or local PostgreSQL)

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd Todo-App
git checkout 001-todo-crud-api
```

### 2. Create Environment Files

Create `.env` at the repository root:

```bash
# Shared secret (generate with: openssl rand -hex 32)
BETTER_AUTH_SECRET=your-32-character-secret-here

# Backend
DATABASE_URL=postgresql://user:password@host/database
CORS_ORIGINS=http://localhost:3000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (after models are created)
# python -m alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Verify Setup

### Backend Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

### Frontend

Open http://localhost:3000 in your browser.

## Development Workflow

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### API Documentation

After starting the backend, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
Todo-App/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── config.py        # Environment config
│   │   ├── database.py      # Database connection
│   │   ├── models/          # SQLModel entities
│   │   ├── routers/         # API endpoints
│   │   ├── middleware/      # JWT auth middleware
│   │   └── schemas/         # Pydantic schemas
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities and API client
│   └── package.json
│
├── specs/001-todo-crud-api/ # Feature specifications
└── .env                     # Environment variables
```

## Common Tasks

### Create a Task (via API)

```bash
# Replace <token> with your JWT token
curl -X POST http://localhost:8000/api/{user_id}/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, eggs, bread"}'
```

### List Tasks

```bash
curl http://localhost:8000/api/{user_id}/tasks \
  -H "Authorization: Bearer <token>"
```

## Troubleshooting

### Database Connection Issues

1. Verify `DATABASE_URL` in `.env`
2. Check Neon dashboard for connection limits
3. Ensure IP is allowed in Neon firewall

### JWT Verification Failures

1. Ensure `BETTER_AUTH_SECRET` matches in both frontend and backend
2. Check token expiration
3. Verify token format: `Authorization: Bearer <token>`

### CORS Errors

1. Verify `CORS_ORIGINS` includes frontend URL
2. Check browser console for specific CORS error
3. Restart backend after changing CORS settings

## Next Steps

1. Run `/sp.tasks` to generate implementation task list
2. Implement tasks in priority order (P1 first)
3. Use specialized agents as defined in CLAUDE.md
