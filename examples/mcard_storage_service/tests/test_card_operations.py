import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_card_flow(async_client: AsyncClient, auth_headers):
    """Test the complete flow of creating and retrieving a card."""
    async for client in async_client:
        # Create a card
        create_response = await client.post(
            "/cards/",
            json={"content": "Test content"},
            headers=auth_headers
        )
        assert create_response.status_code == 201
        card_hash = create_response.json()["hash"]

        # Retrieve the card
        get_response = await client.get(f"/cards/{card_hash}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["content"] == "Test content"

@pytest.mark.asyncio
async def test_list_cards(async_client: AsyncClient, auth_headers):
    """Test listing cards with various filters."""
    async for client in async_client:
        # Create multiple cards
        contents = ["First card", "Second card", "Another test"]
        for content in contents:
            response = await client.post(
                "/cards/",
                json={"content": content},
                headers=auth_headers
            )
            assert response.status_code == 201

        # List all cards
        list_response = await client.get("/cards/", headers=auth_headers)
        assert list_response.status_code == 200
        cards = list_response.json()
        assert len(cards) >= len(contents)

@pytest.mark.asyncio
async def test_delete_card(async_client: AsyncClient, auth_headers):
    """Test deleting a card."""
    async for client in async_client:
        # Create a card
        create_response = await client.post(
            "/cards/",
            json={"content": "Card to delete"},
            headers=auth_headers
        )
        assert create_response.status_code == 201
        card_hash = create_response.json()["hash"]

        # Delete the card
        delete_response = await client.delete(f"/cards/{card_hash}", headers=auth_headers)
        assert delete_response.status_code == 204

        # Verify card is deleted
        get_response = await client.get(f"/cards/{card_hash}", headers=auth_headers)
        assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_error_handling(async_client: AsyncClient, auth_headers):
    """Test various error scenarios."""
    async for client in async_client:
        # Test invalid hash
        response = await client.get(
            "/cards/invalid_hash",
            headers=auth_headers
        )
        assert response.status_code == 404

        # Test invalid request body
        response = await client.post(
            "/cards/",
            json={},  # Missing required content
            headers=auth_headers
        )
        assert response.status_code == 422

        # Test unauthorized access
        response = await client.get("/cards/", headers={})
        assert response.status_code == 401
