from sqlmodel import SQLModel, create_engine, Session
from app.config import get_settings
import os

settings = get_settings()

os.makedirs("./data", exist_ok=True)

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
