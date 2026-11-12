import pytest

from app import create_app
from app.models import db
from app.seed import DEMO_PASSWORD


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    def do_login(username, password=DEMO_PASSWORD):
        return client.post("/login", data={"username": username, "password": password})
    return do_login