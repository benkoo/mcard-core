import pytest
import os
import uvicorn
from unittest.mock import patch, MagicMock
import mcard_storage_service

def test_service_config_defaults():
    """Test service configuration with default values."""
    with patch('uvicorn.run') as mock_run:
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Call the function that would be in __main__
            host = os.getenv("MCARD_SERVICE_HOST", "0.0.0.0")
            port = int(os.getenv("MCARD_SERVICE_PORT", "8000"))
            workers = int(os.getenv("MCARD_SERVICE_WORKERS", "4"))
            log_level = os.getenv("MCARD_SERVICE_LOG_LEVEL", "info").lower()
            
            # Run uvicorn
            uvicorn.run(
                "mcard_storage_service:app",
                host=host,
                port=port,
                workers=workers,
                log_level=log_level
            )
            
            # Check if uvicorn.run was called with default values
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            
            assert kwargs['host'] == '0.0.0.0'
            assert kwargs['port'] == 8000
            assert kwargs['workers'] == 4
            assert kwargs['log_level'] == 'info'

def test_service_config_custom():
    """Test service configuration with custom environment variables."""
    with patch('uvicorn.run') as mock_run:
        # Set custom environment variables
        env_vars = {
            'MCARD_SERVICE_HOST': '127.0.0.1',
            'MCARD_SERVICE_PORT': '5000',
            'MCARD_SERVICE_WORKERS': '2',
            'MCARD_SERVICE_LOG_LEVEL': 'debug'
        }
        with patch.dict(os.environ, env_vars, clear=True):
            # Call the function that would be in __main__
            host = os.getenv("MCARD_SERVICE_HOST", "0.0.0.0")
            port = int(os.getenv("MCARD_SERVICE_PORT", "8000"))
            workers = int(os.getenv("MCARD_SERVICE_WORKERS", "4"))
            log_level = os.getenv("MCARD_SERVICE_LOG_LEVEL", "info").lower()
            
            # Run uvicorn
            uvicorn.run(
                "mcard_storage_service:app",
                host=host,
                port=port,
                workers=workers,
                log_level=log_level
            )
            
            # Check if uvicorn.run was called with custom values
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            
            assert kwargs['host'] == '127.0.0.1'
            assert kwargs['port'] == 5000
            assert kwargs['workers'] == 2
            assert kwargs['log_level'] == 'debug'

def test_service_config_invalid_port():
    """Test service configuration with invalid port number."""
    with patch('uvicorn.run') as mock_run:
        # Set invalid port
        env_vars = {'MCARD_SERVICE_PORT': 'invalid'}
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                port = int(os.getenv("MCARD_SERVICE_PORT", "8000"))
            
            # Verify uvicorn.run was not called
            mock_run.assert_not_called()

def test_service_config_invalid_workers():
    """Test service configuration with invalid workers count."""
    with patch('uvicorn.run') as mock_run:
        # Set invalid workers count
        env_vars = {'MCARD_SERVICE_WORKERS': 'invalid'}
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                workers = int(os.getenv("MCARD_SERVICE_WORKERS", "4"))
            
            # Verify uvicorn.run was not called
            mock_run.assert_not_called()
