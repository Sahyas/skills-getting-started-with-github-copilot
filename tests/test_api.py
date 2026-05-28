import copy
import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: snapshot global activities and restore after each test to keep tests isolated."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original))


client = TestClient(app_module.app)


def test_get_activities_returns_list():
    # Arrange: TestClient (above)

    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect a known activity
    assert "Chess Club" in data


def test_signup_adds_participant_and_is_idempotent():
    # Arrange
    activity = "Math Club"
    email = "tester@example.com"

    # Ensure participant not present first
    before = client.get(f"/activities").json()[activity]["participants"]
    assert all(email.lower() != p.strip().lower() for p in before)

    # Act - first signup
    resp = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body.get("message", "")

    # Act - duplicate signup should be rejected
    dup = client.post(f"/activities/{activity}/signup?email={email}")
    assert dup.status_code == 400
    assert dup.json().get("detail") is not None


def test_remove_participant():
    # Arrange
    activity = "Art Club"
    email = "zoe@mergington.edu"

    # Precondition: participant exists
    data = client.get("/activities").json()
    assert email.lower() in [p.strip().lower() for p in data[activity]["participants"]]

    # Act
    resp = client.delete(f"/activities/{activity}/participants?email={email}")

    # Assert
    assert resp.status_code == 200
    assert "Removed" in resp.json().get("message", "")

    # Confirm removal
    after = client.get("/activities").json()[activity]["participants"]
    assert email.lower() not in [p.strip().lower() for p in after]
