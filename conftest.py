import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database import Base, get_db
from main import app

import os
from dotenv import load_dotenv

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL não configurada")

engine_teste = create_engine(TEST_DATABASE_URL)
SessionTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)

@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine_teste)
    session = SessionTeste()
    try:
        yield session
    finally: 
        session.close()
        Base.metadata.drop_all(bind = engine_teste)

@pytest.fixture()
def client(db_session):
    def sobrescrever_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = sobrescrever_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()