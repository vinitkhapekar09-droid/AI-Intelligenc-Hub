from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings


def _sqlite_fallback_url() -> str:
    fallback_dir = Path(__file__).resolve().parents[2] / ".local"
    fallback_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{fallback_dir / 'daily_digest.db'}"


def resolve_database_url() -> str:
    database_url = settings.DATABASE_URL

    if database_url.startswith("sqlite"):
        return database_url

    try:
        resolved_engine = create_engine(database_url, pool_pre_ping=True)
        with resolved_engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return database_url
    except OperationalError as exc:
        if settings.ENVIRONMENT.lower() == "production":
            raise

        fallback_url = _sqlite_fallback_url()
        print(
            "[startup] Primary database unavailable; "
            f"falling back to SQLite at {fallback_url}: {exc}"
        )
        return fallback_url


def _create_engine():
    resolved_database_url = resolve_database_url()

    if resolved_database_url.startswith("sqlite"):
        return create_engine(
            resolved_database_url,
            connect_args={"check_same_thread": False},
        )

    return create_engine(resolved_database_url, pool_pre_ping=True)


engine = _create_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
