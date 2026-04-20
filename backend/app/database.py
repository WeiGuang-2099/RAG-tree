from sqlmodel import SQLModel, create_engine, Session
from app.config import get_settings
from app.services.ai_service import AiService
from app.services.graph_service import GraphService
import os

settings = get_settings()

os.makedirs("./data", exist_ok=True)

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)

# Singleton service instances
ai_service_instance = AiService()
graph_service_instance = GraphService()


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def get_ai_service() -> AiService:
    return ai_service_instance


def get_graph_service() -> GraphService:
    return graph_service_instance
