import pytest
from httpx import AsyncClient
from mcard_service.api_service import app

@pytest.mark.asyncio
async def test_create_card():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/cards/", json={"content": "Test content"})
    assert response.status_code == 200
    assert "hash" in response.json()

@pytest.mark.asyncio
async def test_get_card():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First create a card
        create_response = await ac.post("/cards/", json={"content": "Test content"})
        hash_str = create_response.json()["hash"]

        # Retrieve the created card
        response = await ac.get(f"/cards/{hash_str}")
    assert response.status_code == 200
    assert response.json()["content"] == "Test content"

@pytest.mark.asyncio
async def test_list_cards():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/cards/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_delete_card():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First create a card
        create_response = await ac.post("/cards/", json={"content": "Test content"})
        hash_str = create_response.json()["hash"]

        # Delete the created card
        delete_response = await ac.delete(f"/cards/{hash_str}")
    assert delete_response.status_code == 200
    assert delete_response.json()["detail"] == "Card deleted successfully"
