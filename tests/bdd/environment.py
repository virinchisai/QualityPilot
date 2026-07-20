from fastapi.testclient import TestClient

from app.demo_app.main import app
from qualitypilot.database import Base, engine


def before_scenario(context, _scenario):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    context.client_manager = TestClient(app)
    context.client = context.client_manager.__enter__()


def after_scenario(context, _scenario):
    context.client_manager.__exit__(None, None, None)
