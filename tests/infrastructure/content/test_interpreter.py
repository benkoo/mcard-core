"""
Tests for content type detection and validation service.
"""
import pytest
from mcard.infrastructure.content.interpreter import ContentTypeInterpreter
from mcard.infrastructure.persistence.sqlite import SQLiteRepository
from mcard.domain.models.exceptions import ValidationError

@pytest.fixture
def interpreter():
    return ContentTypeInterpreter()

def test_detect_by_signature_png():
    """Test PNG signature detection."""
    interpreter = ContentTypeInterpreter()
    content = b'\x89PNG\r\n\x1a\n' + b'some PNG data'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'image/png'
    assert ext == 'png'

def test_detect_by_signature_jpeg():
    """Test JPEG signature detection."""
    interpreter = ContentTypeInterpreter()
    content = b'\xff\xd8\xff' + b'some JPEG data'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'image/jpeg'
    assert ext == 'jpg'

def test_detect_xml_content():
    """Test XML content detection."""
    interpreter = ContentTypeInterpreter()
    content = b'<?xml version="1.0" encoding="UTF-8"?><root></root>'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'application/xml'
    assert ext == 'xml'

def test_detect_svg_content():
    """Test SVG content detection."""
    interpreter = ContentTypeInterpreter()
    content = b'''<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"></svg>'''
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'image/svg+xml'
    assert ext == 'svg'

def test_detect_json_content():
    """Test JSON content detection."""
    interpreter = ContentTypeInterpreter()
    content = b'{"key": "value"}'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'application/json'
    assert ext == 'json'

def test_detect_text_content():
    """Test plain text content detection."""
    interpreter = ContentTypeInterpreter()
    content = b'Hello, world!'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'text/plain'
    assert ext == 'txt'

def test_detect_binary_content():
    """Test binary content detection."""
    interpreter = ContentTypeInterpreter()
    # Create some binary content with control characters
    content = bytes(range(0, 32))
    assert interpreter.is_binary_content(content)

def test_validate_content_valid_json():
    """Test validation of valid JSON content."""
    interpreter = ContentTypeInterpreter()
    content = b'{"key": "value"}'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'application/json'
    assert ext == 'json'

def test_validate_content_invalid_json():
    """Test validation of invalid JSON content."""
    interpreter = ContentTypeInterpreter()
    content = b'{"key": invalid}'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'text/plain'  # Invalid JSON is treated as text
    assert ext == 'txt'

def test_validate_content_valid_xml():
    """Test validation of valid XML content."""
    interpreter = ContentTypeInterpreter()
    content = b'<?xml version="1.0"?><root></root>'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'application/xml'
    assert ext == 'xml'

def test_validate_content_invalid_xml():
    """Test validation of invalid XML content."""
    interpreter = ContentTypeInterpreter()
    content = b'<?xml version="1.0"?><root>'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'text/plain'  # Invalid XML is treated as text
    assert ext == 'txt'

def test_validate_content_empty():
    """Test validation of empty content."""
    interpreter = ContentTypeInterpreter()
    with pytest.raises(ValidationError, match="Content must be string or bytes"):
        interpreter.detect_content_type(None)

def test_detect_type_string_content():
    """Test type detection with string content."""
    interpreter = ContentTypeInterpreter()
    mime_type, ext = interpreter.detect_content_type("Hello, world!")
    assert mime_type == 'text/plain'
    assert ext == 'txt'

def test_is_binary_content_string():
    """Test binary detection with string content."""
    interpreter = ContentTypeInterpreter()
    assert not interpreter.is_binary_content("Hello, world!")

def test_is_binary_content_binary():
    """Test binary detection with binary content."""
    interpreter = ContentTypeInterpreter()
    content = bytes(range(256))  # Create binary content
    assert interpreter.is_binary_content(content)

def test_detect_pdf_content():
    """Test PDF content detection."""
    interpreter = ContentTypeInterpreter()
    content = b'%PDF-1.4\n' + b'some PDF data'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'application/pdf'
    assert ext == 'pdf'

def test_detect_zip_content():
    """Test ZIP content detection."""
    interpreter = ContentTypeInterpreter()
    content = b'PK\x03\x04' + b'some ZIP data'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'application/zip'
    assert ext == 'zip'

def test_detect_gif_content():
    """Test GIF content detection."""
    interpreter = ContentTypeInterpreter()
    content = b'GIF89a' + b'some GIF data'
    mime_type, ext = interpreter.detect_content_type(content)
    assert mime_type == 'image/gif'
    assert ext == 'gif'

def test_malformed_xml_content():
    """Test handling of malformed XML content."""
    interpreter = ContentTypeInterpreter()
    content = b'<?xml version="1.0"?><root><unclosed>'
    with pytest.raises(ValidationError, match="Invalid XML content"):
        interpreter.validate_content(content)

def test_malformed_json_with_comments():
    """Test handling of JSON with comments (invalid JSON)."""
    interpreter = ContentTypeInterpreter()
    content = b'''{
        // This is a comment
        "key": "value"
    }'''
    with pytest.raises(ValidationError, match="Invalid JSON content"):
        interpreter.validate_content(content)

def test_truncated_png_content():
    """Test handling of truncated PNG content."""
    interpreter = ContentTypeInterpreter()
    content = b'\x89PNG\r\n\x1a\n'  # Only header, no actual PNG data
    mime_type, ext = interpreter.detect_content_type(content)
    # Should still detect as PNG based on signature
    assert mime_type == 'image/png'
    assert ext == 'png'
    # But validation should fail
    with pytest.raises(ValidationError, match="Invalid content"):
        interpreter.validate_content(content)

def test_mixed_content_type():
    """Test handling of content with mixed or ambiguous type signatures."""
    interpreter = ContentTypeInterpreter()
    # Content that starts with XML but contains binary data
    content = b'<?xml version="1.0"?><root>' + b'\x89PNG\r\n\x1a\n'
    mime_type, ext = interpreter.detect_content_type(content)
    # Should detect as XML since it starts with XML signature
    assert mime_type == 'application/xml'
    assert ext == 'xml'
    # But validation should fail due to mixed content
    with pytest.raises(ValidationError):
        interpreter.validate_content(content)

def test_zero_byte_content():
    """Test handling of zero-byte content."""
    interpreter = ContentTypeInterpreter()
    content = b''
    with pytest.raises(ValidationError, match="Empty content"):
        interpreter.validate_content(content)

def test_get_default_extension():
    """Test default file extension retrieval based on MIME type."""
    interpreter = ContentTypeInterpreter()
    # Test cases for known MIME types
    assert interpreter.get_default_extension('application/pdf') == 'pdf'
    assert interpreter.get_default_extension('text/plain') == 'txt'
    assert interpreter.get_default_extension('image/png') == 'png'
    assert interpreter.get_default_extension('image/jpeg') == 'jpg'
    assert interpreter.get_default_extension('video/quicktime') == 'mov'
    assert interpreter.get_default_extension('application/x-tex') == 'tex'
    assert interpreter.get_default_extension('application/3d-obj') == 'obj'
    assert interpreter.get_default_extension('image/svg+xml') == 'svg'
    assert interpreter.get_default_extension('text/x-mermaid') == 'mmd'
    assert interpreter.get_default_extension('image/vnd.dxf') == 'dxf'
    assert interpreter.get_default_extension('image/vnd.djvu') == 'djv'
    # Test case for an unknown MIME type
    assert interpreter.get_default_extension('unknown/type') == ''
