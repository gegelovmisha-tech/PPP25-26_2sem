import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

def test_create_source():
    response = client.post("/sources/", json={"name": "Test Source", "url": "https://test.com", "type": "api"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Source"

def test_get_sources():
    client.post("/sources/", json={"name": "Source 1"})
    client.post("/sources/", json={"name": "Source 2"})
    response = client.get("/sources/")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_create_item():
    client.post("/sources/", json={"name": "Test Source"})
    response = client.post("/items/", json={"name": "Test Item", "price": 99.99, "category": "Test", "source_id": 1})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"

def test_get_item_not_found():
    response = client.get("/items/999")
    assert response.status_code == 404

def test_update_item_patch():
    client.post("/sources/", json={"name": "Test Source"})
    client.post("/items/", json={"name": "Old", "price": 10, "source_id": 1})
    response = client.patch("/items/1", json={"name": "New"})
    assert response.status_code == 200
    assert response.json()["name"] == "New"

def test_delete_item():
    client.post("/sources/", json={"name": "Test Source"})
    client.post("/items/", json={"name": "To Delete", "price": 10, "source_id": 1})
    response = client.delete("/items/1")
    assert response.status_code == 204
    response = client.get("/items/1")
    assert response.status_code == 404

def test_filter_items():
    client.post("/sources/", json={"name": "Test Source"})
    client.post("/items/", json={"name": "Phone", "category": "Electronics", "source_id": 1})
    client.post("/items/", json={"name": "Chair", "category": "Furniture", "source_id": 1})
    response = client.get("/items/?category=Electronics")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_create_task():
    response = client.post("/tasks/rebuild_stats")
    assert response.status_code == 200
    assert "task_id" in response.json()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
