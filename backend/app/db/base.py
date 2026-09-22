"""Import Base so alembic/seed can discover all tables."""
from app.db.session import Base, engine  # noqa: F401

from app.models.models import *  # noqa: F401,F403


def create_all() -> None:
    Base.metadata.create_all(bind=engine)