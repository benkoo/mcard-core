import pytest
from fastapi.testclient import TestClient
from mcard.interfaces.api.server import app

client = TestClient(app)

api_key = "your_api_key_here"  # Set your actual API key


def test_server_initialization():
    """Test if the server initializes without errors."""
    response = client.get('/health', headers={'Authorization': f'Bearer {api_key}'})  # Test health check endpoint
    assert response.status_code == 200

    response = client.post('/cards/', json={'content': 'Test card content'}, headers={'Authorization': f'Bearer {api_key}'})  # Test create card
    assert response.status_code == 201
    card_hash = response.json()['hash']  # Get the card hash from response
    assert 'hash' in response.json()  # Check for card hash in response

    response = client.get(f'/cards/{card_hash}', headers={'Authorization': f'Bearer {api_key}'})  # Test get card by hash
    assert response.status_code == 200

    response = client.get('/cards/?page=1&page_size=10', headers={'Authorization': f'Bearer {api_key}'})  # Test list cards
    assert response.status_code == 200

    response = client.delete(f'/cards/{card_hash}', headers={'Authorization': f'Bearer {api_key}'})  # Test remove card by hash
    assert response.status_code == 200

    response = client.delete('/cards/', headers={'Authorization': f'Bearer {api_key}'})  # Test delete all cards
    assert response.status_code == 200

    response = client.get('/health', headers={'Authorization': f'Bearer {api_key}'})  # Test health check
    assert response.status_code == 200


def test_api_endpoint():
    """Test a specific API endpoint."""
    response = client.get('/cards/', headers={'Authorization': f'Bearer {api_key}'})  # Test cards endpoint
    assert response.status_code == 200


def test_cors():
    """Test CORS configuration."""
    response = client.options('/cards/', headers={'Authorization': f'Bearer {api_key}'})  # Test CORS for cards endpoint
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert response.headers["Access-Control-Allow-Origin"] == "*"  # Adjust based on your CORS settings
