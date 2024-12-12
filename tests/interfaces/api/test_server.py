import pytest
from fastapi.testclient import TestClient
from mcard.interfaces.api.server import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_card():
    response = client.post("/cards/", json={"content": "Test content"})
    assert response.status_code == 200
    assert "hash" in response.json()


def test_get_card():
    create_response = client.post("/cards/", json={"content": "Test content"})
    card_hash = create_response.json()["hash"]
    response = client.get(f"/cards/{card_hash}")
    assert response.status_code == 200
    assert response.json()["hash"] == card_hash


def test_list_cards():
    response = client.get("/cards/?page=1&page_size=10")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_delete_card():
    create_response = client.post("/cards/", json={"content": "Test content"})
    card_hash = create_response.json()["hash"]
    delete_response = client.delete(f"/cards/{card_hash}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Card deleted"}


def test_shutdown():
    response = client.post("/shutdown")
    assert response.status_code == 200
    assert response.json() == {"message": "Server shutting down"}
