"""
Tests for the MCard CLI interface.
"""
import pytest
from datetime import datetime, timezone
from click.testing import CliRunner
from unittest.mock import AsyncMock, patch, MagicMock

from mcard.domain.models.card import MCard
from mcard.infrastructure.persistence.sqlite import SQLiteRepository
from mcard.interfaces.cli.commands import cli

# Test data
TEST_CONTENT = "Test content"
TEST_HASH = "test_hash_123"
TEST_TIME = datetime.now(timezone.utc).isoformat()
TEST_CARD = MCard(content=TEST_CONTENT, hash=TEST_HASH, g_time=TEST_TIME)

@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()

@pytest.fixture
def mock_repo():
    """Create a mock repository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.get = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_by_time_range = AsyncMock()
    return repo

@pytest.fixture
def mock_get_repo(mock_repo):
    """Mock the get_repository function."""
    with patch('mcard.interfaces.cli.commands.get_repository', return_value=mock_repo):
        yield mock_repo

def test_create_command(runner, mock_get_repo):
    """Test the create command."""
    mock_get_repo.save.return_value = None
    result = runner.invoke(cli, ['create', TEST_CONTENT])
    
    assert result.exit_code == 0
    assert "Created card with hash:" in result.output
    assert "Global time:" in result.output
    
    mock_get_repo.save.assert_called_once()

def test_get_command_success(runner, mock_get_repo):
    """Test the get command with an existing card."""
    mock_get_repo.get.return_value = TEST_CARD
    result = runner.invoke(cli, ['get', TEST_HASH])
    
    assert result.exit_code == 0
    assert TEST_HASH in result.output
    assert TEST_CONTENT in result.output
    assert TEST_TIME in result.output
    
    mock_get_repo.get.assert_called_once_with(TEST_HASH)

def test_get_command_not_found(runner, mock_get_repo):
    """Test the get command with a non-existent card."""
    mock_get_repo.get.return_value = None
    result = runner.invoke(cli, ['get', TEST_HASH])
    
    assert result.exit_code == 0
    assert "Card not found" in result.output
    
    mock_get_repo.get.assert_called_once_with(TEST_HASH)

def test_list_command_no_filters(runner, mock_get_repo):
    """Test the list command without filters."""
    mock_get_repo.get_all.return_value = [TEST_CARD]
    result = runner.invoke(cli, ['list'])
    
    assert result.exit_code == 0
    assert TEST_HASH in result.output
    assert TEST_CONTENT in result.output
    assert TEST_TIME in result.output
    
    mock_get_repo.get_all.assert_called_once_with(None, None)

def test_list_command_with_time_range(runner, mock_get_repo):
    """Test the list command with time range filters."""
    mock_get_repo.get_by_time_range.return_value = [TEST_CARD]
    start_time = "2024-01-01T00:00:00Z"
    end_time = "2024-01-02T00:00:00Z"
    
    result = runner.invoke(cli, [
        'list',
        '--start-time', start_time,
        '--end-time', end_time
    ])
    
    assert result.exit_code == 0
    assert TEST_HASH in result.output
    assert TEST_CONTENT in result.output
    
    mock_get_repo.get_by_time_range.assert_called_once()

def test_list_command_with_pagination(runner, mock_get_repo):
    """Test the list command with pagination."""
    mock_get_repo.get_all.return_value = [TEST_CARD]
    result = runner.invoke(cli, [
        'list',
        '--limit', '10',
        '--offset', '0'
    ])
    
    assert result.exit_code == 0
    assert TEST_HASH in result.output
    assert TEST_CONTENT in result.output
    
    mock_get_repo.get_all.assert_called_once_with(10, 0)
