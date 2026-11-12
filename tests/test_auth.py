from app.models import User


def test_pages_need_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.location


def test_api_without_login_returns_no_patients(client):
    response = client.post("/api/sync", json={"updates": []})
    assert response.status_code == 401
    assert response.get_json()["mothers"] == []


def test_five_wrong_passwords_lock_the_account(client, login):
    for _ in range(5):
        login("nurse.alice", "wrong-password")
    assert User.query.filter_by(username="nurse.alice").first().is_locked()

    response = login("nurse.alice")
    assert response.status_code == 200
    assert b"locked" in response.data


def test_passwords_are_stored_as_hashes(app):
    user = User.query.filter_by(username="nurse.alice").first()
    assert "MamaTrack2026" not in user.password_hash


def test_new_signup_waits_for_approval(client, login):
    client.post("/signup", data={"full_name": "New Nurse", "username": "new.nurse",
                                 "role": "nurse", "facility_id": "1",
                                 "password": "longpass1", "confirm": "longpass1"})
    response = login("new.nurse", "longpass1")
    assert b"waiting for supervisor approval" in response.data


def test_chw_cannot_register_mothers(client, login):
    login("chw.jean")
    assert client.get("/mothers/new").status_code == 403