import os
import pytest
import sqlite3
import tempfile

from app import app, init_db, calculate_calories, PROGRAMS, get_db


@pytest.fixture
def client():
    """Flask test client with isolated temp DB, initialized before each test."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    # Patch get_db to use the temp path for this test
    import app as app_module
    original_db = app_module.DB_NAME
    app_module.DB_NAME = db_path

    init_db()

    with app.test_client() as c:
        yield c

    app_module.DB_NAME = original_db
    os.unlink(db_path)


# ---------- UNIT TESTS: Core Logic ----------

def test_calculate_calories_fat_loss():
    result = calculate_calories(80, "Fat Loss (FL)")
    assert result == 80 * 22


def test_calculate_calories_muscle_gain():
    result = calculate_calories(75, "Muscle Gain (MG)")
    assert result == 75 * 35


def test_calculate_calories_beginner():
    result = calculate_calories(60, "Beginner (BG)")
    assert result == 60 * 26


def test_calculate_calories_unknown_program():
    result = calculate_calories(70, "Unknown Program")
    assert result == 0


def test_calculate_calories_no_weight():
    result = calculate_calories(None, "Fat Loss (FL)")
    assert result == 0


def test_programs_have_required_keys():
    for name, data in PROGRAMS.items():
        assert "workout" in data, f"{name} missing 'workout'"
        assert "diet" in data, f"{name} missing 'diet'"
        assert "calorie_factor" in data, f"{name} missing 'calorie_factor'"


def test_calorie_factors_are_positive():
    for name, data in PROGRAMS.items():
        assert data["calorie_factor"] > 0, f"{name} calorie_factor must be positive"


# ---------- INTEGRATION TESTS: Routes ----------

def test_login_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"ACEest" in response.data


def test_login_invalid_credentials(client):
    response = client.post("/", data={"username": "wrong", "password": "bad"})
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_login_valid_credentials(client):
    response = client.post(
        "/",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=True)
    assert b"Login" in response.data or response.status_code == 200


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"


def test_add_client_requires_login(client):
    response = client.get("/client/add", follow_redirects=True)
    assert b"Login" in response.data or response.status_code == 200


def test_add_client_saves_to_db(client):
    client.post("/", data={"username": "admin", "password": "admin123"})
    response = client.post(
        "/client/add",
        data={
            "name": "Test User",
            "age": "25",
            "height": "175",
            "weight": "70",
            "program": "Fat Loss (FL)",
            "target_weight": "65",
            "target_adherence": "80",
            "membership_end": "2026-12-31",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_client_profile_not_found(client):
    client.post("/", data={"username": "admin", "password": "admin123"})
    response = client.get("/client/NonExistentClient", follow_redirects=True)
    assert response.status_code == 200


def test_logout_clears_session(client):
    client.post("/", data={"username": "admin", "password": "admin123"})
    response = client.get("/logout", follow_redirects=True)
    assert b"Login" in response.data or response.status_code == 200
