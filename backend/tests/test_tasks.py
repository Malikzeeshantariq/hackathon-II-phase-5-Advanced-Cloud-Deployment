"""T045, T046, T047: Task endpoint tests.

Spec Reference: quickstart.md - Running Tests
Validates: User isolation (SC-005), Auth enforcement (SC-003, SC-004)
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import Depends
from sqlmodel import Session

from app.main import app
from app.database import get_session
from app.middleware.auth import TokenPayload, get_current_user


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client: TestClient):
        """T045: Backend starts and responds to health check."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def create_mock_user(user_id: str):
    """Create a mock current user dependency."""
    def mock_get_current_user():
        return TokenPayload(user_id=user_id)
    return mock_get_current_user


class TestTaskEndpoints:
    """Test task CRUD endpoints with mocked authentication."""

    @pytest.fixture(autouse=True)
    def mock_auth(self, client: TestClient):
        """Override JWT authentication for all tests in this class."""
        app.dependency_overrides[get_current_user] = create_mock_user("user-123")
        yield
        # Clean up the specific override, but keep session override
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

    def test_create_task(self, client: TestClient):
        """Test creating a new task."""
        response = client.post(
            "/api/user-123/tasks",
            json={"title": "Test task", "description": "Test description"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test task"
        assert data["description"] == "Test description"
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_task_minimal(self, client: TestClient):
        """Test creating a task with only title."""
        response = client.post(
            "/api/user-123/tasks",
            json={"title": "Minimal task"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal task"
        assert data["description"] is None

    def test_create_task_validation_error(self, client: TestClient):
        """T042: Test 422 validation error for empty title."""
        response = client.post(
            "/api/user-123/tasks",
            json={"title": ""},
        )
        assert response.status_code == 422

    def test_create_task_title_too_long(self, client: TestClient):
        """Test 422 validation error for title exceeding 255 characters."""
        long_title = "x" * 256
        response = client.post(
            "/api/user-123/tasks",
            json={"title": long_title},
        )
        assert response.status_code == 422

    def test_create_task_description_too_long(self, client: TestClient):
        """Test 422 validation error for description exceeding 2000 characters."""
        long_description = "x" * 2001
        response = client.post(
            "/api/user-123/tasks",
            json={"title": "Valid title", "description": long_description},
        )
        assert response.status_code == 422

    def test_list_tasks_empty(self, client: TestClient):
        """Test listing tasks when none exist."""
        response = client.get("/api/user-123/tasks")
        assert response.status_code == 200
        assert response.json() == {"tasks": []}

    def test_list_tasks(self, client: TestClient):
        """Test listing tasks after creation."""
        # Create a task first
        client.post("/api/user-123/tasks", json={"title": "Task 1"})
        client.post("/api/user-123/tasks", json={"title": "Task 2"})

        response = client.get("/api/user-123/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2

    def test_get_task(self, client: TestClient):
        """Test getting a specific task."""
        # Create a task first
        create_response = client.post(
            "/api/user-123/tasks",
            json={"title": "Test task"},
        )
        task_id = create_response.json()["id"]

        response = client.get(f"/api/user-123/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Test task"

    def test_get_task_not_found(self, client: TestClient):
        """T041: Test 404 for non-existent task."""
        response = client.get(
            "/api/user-123/tasks/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_update_task(self, client: TestClient):
        """Test updating a task."""
        # Create a task first
        create_response = client.post(
            "/api/user-123/tasks",
            json={"title": "Original title"},
        )
        task_id = create_response.json()["id"]

        response = client.put(
            f"/api/user-123/tasks/{task_id}",
            json={"title": "Updated title", "description": "New description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated title"
        assert data["description"] == "New description"

    def test_complete_task(self, client: TestClient):
        """Test toggling task completion."""
        # Create a task first
        create_response = client.post(
            "/api/user-123/tasks",
            json={"title": "Test task"},
        )
        task_id = create_response.json()["id"]
        assert create_response.json()["completed"] is False

        # Toggle to complete
        response = client.patch(f"/api/user-123/tasks/{task_id}/complete")
        assert response.status_code == 200
        assert response.json()["completed"] is True

        # Toggle back to incomplete
        response = client.patch(f"/api/user-123/tasks/{task_id}/complete")
        assert response.status_code == 200
        assert response.json()["completed"] is False

    def test_delete_task(self, client: TestClient):
        """Test deleting a task."""
        # Create a task first
        create_response = client.post(
            "/api/user-123/tasks",
            json={"title": "Test task"},
        )
        task_id = create_response.json()["id"]

        # Delete the task
        response = client.delete(f"/api/user-123/tasks/{task_id}")
        assert response.status_code == 204

        # Verify it's deleted
        response = client.get(f"/api/user-123/tasks/{task_id}")
        assert response.status_code == 404


class TestUserIsolation:
    """T046: Test user isolation - users cannot see each other's tasks."""

    def test_user_cannot_access_other_user_tasks(self, client: TestClient):
        """Verify that users can only access their own tasks."""
        # User-123 creating a task
        app.dependency_overrides[get_current_user] = create_mock_user("user-123")
        create_response = client.post(
            "/api/user-123/tasks",
            json={"title": "User 123's task"},
        )
        task_id = create_response.json()["id"]

        # User-456 trying to access user-123's task
        app.dependency_overrides[get_current_user] = create_mock_user("user-456")

        # Try to get the task - should be 404 (not found for this user)
        response = client.get(f"/api/user-456/tasks/{task_id}")
        assert response.status_code == 404

        # Clean up
        del app.dependency_overrides[get_current_user]

    def test_url_user_id_must_match_jwt(self, client: TestClient):
        """T040: Test 403 when URL user_id doesn't match JWT."""
        app.dependency_overrides[get_current_user] = create_mock_user("user-123")

        # Try to access different user's endpoint
        response = client.get("/api/user-456/tasks")
        assert response.status_code == 403
        assert response.json()["detail"] == "Forbidden"

        # Clean up
        del app.dependency_overrides[get_current_user]


class TestAuthEnforcement:
    """T047: Test authentication enforcement."""

    def test_missing_auth_header(self, client: TestClient):
        """T039: Test 401 when no Authorization header is provided."""
        # Clear any auth overrides to test real auth behavior
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get("/api/user-123/tasks")
        # Spec AR-002: 401 Unauthorized for missing/invalid JWT
        assert response.status_code == 401

    def test_invalid_token_format(self, client: TestClient):
        """Test 401 for invalid token format."""
        # Clear any auth overrides to test real auth behavior
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.get(
            "/api/user-123/tasks",
            headers={"Authorization": "InvalidFormat"},
        )
        # Spec AR-002: 401 Unauthorized for missing/invalid JWT
        assert response.status_code == 401
