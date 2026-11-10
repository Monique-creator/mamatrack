import os
from datetime import timedelta


def database_url():
    url = os.environ.get("DATABASE_URL", "sqlite:///mamatrack.db")
    # Hosts hand out postgres:// or postgresql://; point SQLAlchemy at psycopg2 explicitly.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return url.replace(prefix, "postgresql+psycopg2://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret")
    SQLALCHEMY_DATABASE_URI = database_url()
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("RENDER") is not None

    FOLLOW_UP_DAYS = 42
    DUE_SOON_DAYS = 7
    MAX_FAILED_LOGINS = 5
    LOCK_MINUTES = 15