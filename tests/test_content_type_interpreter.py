import pytest
from mcard.domain.dependency.interpreter import ContentTypeInterpreter

def test_webp_detection():
    # Test WebP detection with various WebP file signatures
    webp_signatures = [
        b'RIFF____WEBP',  # Typical WebP file signature
        b'WEBP',          # Alternative signature
    ]
    
    for signature in webp_signatures:
        content_type, ext = ContentTypeInterpreter.detect_content_type(signature)
        assert content_type == 'image/webp', f"Failed to detect WebP for signature {signature}"
        assert ext == 'webp', f"Incorrect extension for WebP signature {signature}"

def test_webp_file_upload():
    # You might want to add a test with an actual WebP file
    # This is a placeholder for a real WebP file test
    pass
