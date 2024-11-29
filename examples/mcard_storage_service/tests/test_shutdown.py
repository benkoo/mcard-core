import pytest
import signal
import sys
from unittest.mock import MagicMock, patch
from mcard_storage_service import handle_shutdown

def test_graceful_shutdown():
    """Test that shutdown handler exits gracefully."""
    with patch('sys.exit') as mock_exit:
        # Create mock frame and signal
        mock_frame = MagicMock()
        
        # Call shutdown handler
        handle_shutdown(signal.SIGTERM, mock_frame)
        
        # Verify sys.exit was called
        mock_exit.assert_called_once_with(0)

def test_shutdown_signal_registration():
    """Test that shutdown signals are properly registered."""
    # We need to reload the module to trigger signal registration
    with patch('signal.signal') as mock_signal:
        import importlib
        import mcard_storage_service
        importlib.reload(mcard_storage_service)
        
        # Verify SIGTERM and SIGINT are registered
        assert mock_signal.call_count >= 2
        calls = mock_signal.call_args_list
        signals_registered = [call[0][0] for call in calls]
        assert signal.SIGTERM in signals_registered
        assert signal.SIGINT in signals_registered
