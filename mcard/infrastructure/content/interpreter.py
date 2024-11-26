"""
Content type detection and validation service.
"""
import json
import mimetypes
import xml.etree.ElementTree as ET
from typing import Any, Dict, Tuple, Union
from ...domain.models.exceptions import ValidationError

class ContentTypeInterpreter:
    """Service for content type detection and validation."""

    # Common file signatures (magic numbers) and their corresponding MIME types
    SIGNATURES: Dict[bytes, str] = {
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'%PDF': 'application/pdf',
        b'PK\x03\x04': 'application/zip',
    }

    # Text-based MIME types
    TEXT_MIME_TYPES = {
        'text/plain',
        'text/html',
        'text/xml',
        'text/csv',
        'text/css',
        'text/javascript',
        'application/json',
        'application/xml',
        'application/x-yaml',
        'application/javascript',
    }

    @staticmethod
    def _detect_by_signature(content: bytes) -> str:
        """Detect MIME type using file signatures."""
        # Check for known file signatures
        for signature, mime_type in ContentTypeInterpreter.SIGNATURES.items():
            if content.startswith(signature):
                return mime_type
        
        # Check for XML signature
        if content.startswith(b'<?xml') or content.lstrip(b' \t\n\r').startswith(b'<'):
            # Further check for SVG
            try:
                text_content = content.decode('utf-8', errors='ignore')
                if ContentTypeInterpreter.is_svg_content(text_content):
                    return 'image/svg+xml'
                return 'application/xml'
            except:
                pass
        
        return 'application/octet-stream'

    @staticmethod
    def detect_content_type(content: Union[str, bytes]) -> Tuple[str, str]:
        """
        Detect content type and suggested extension.
        Returns tuple of (mime_type, extension).
        """
        if isinstance(content, str):
            # Try to parse as JSON
            try:
                json.loads(content)
                return 'application/json', 'json'
            except json.JSONDecodeError:
                pass
            
            # Try to parse as XML
            try:
                # Convert string to bytes for consistent handling
                content_bytes = content.encode('utf-8')
                is_xml = ContentTypeInterpreter.is_xml_content(content_bytes)
                if is_xml:
                    # Check if it's specifically an SVG
                    if ContentTypeInterpreter.is_svg_content(content):
                        return 'image/svg+xml', 'svg'
                    # Generic XML
                    return 'application/xml', 'xml'
            except Exception:
                pass
            
            # Default to text/plain for strings
            return 'text/plain', 'txt'
        
        elif isinstance(content, bytes):
            # Detect MIME type using signatures
            mime_type = ContentTypeInterpreter._detect_by_signature(content)
            
            # If no specific binary format detected, check for text formats
            if mime_type == 'application/octet-stream':
                # Try to decode as UTF-8
                try:
                    text_content = content.decode('utf-8')
                    
                    # Check for JSON
                    try:
                        json.loads(text_content)
                        return 'application/json', 'json'
                    except json.JSONDecodeError:
                        pass
                    
                    # Check for XML
                    if ContentTypeInterpreter.is_xml_content(content):
                        if ContentTypeInterpreter.is_svg_content(text_content):
                            return 'image/svg+xml', 'svg'
                        return 'application/xml', 'xml'
                    
                    # Default to text/plain for decodeable content
                    return 'text/plain', 'txt'
                except UnicodeDecodeError:
                    pass
            
            # Get extension from mime type
            extension = mimetypes.guess_extension(mime_type, strict=False)
            if extension:
                # Remove the leading dot
                extension = extension[1:]
            else:
                # Fallback extensions for common types
                extension = {
                    'image/jpeg': 'jpg',
                    'image/png': 'png',
                    'image/gif': 'gif',
                    'image/svg+xml': 'svg',
                    'application/pdf': 'pdf',
                    'application/json': 'json',
                    'text/plain': 'txt',
                    'text/html': 'html',
                    'application/zip': 'zip',
                    'application/xml': 'xml',
                    'text/xml': 'xml'
                }.get(mime_type, '')
            
            return mime_type, extension
        
        raise ValidationError("Content must be string or bytes")

    @staticmethod
    def is_binary_content(content: Union[str, bytes]) -> bool:
        """
        Determine if content should be treated as binary.
        
        This method uses multiple heuristics:
        1. If content is already a string, it's not binary
        2. For bytes content:
           - Check for known binary signatures
           - Try UTF-8 decoding
           - Analyze content patterns
        """
        if isinstance(content, str):
            return False
        
        if not isinstance(content, (bytes, bytearray)):
            raise ValidationError("Content must be string or bytes")

        # Check for known binary signatures
        mime_type = ContentTypeInterpreter._detect_by_signature(content)
        if mime_type != 'application/octet-stream':
            return mime_type not in ContentTypeInterpreter.TEXT_MIME_TYPES
        
        # Try to decode as UTF-8
        try:
            content.decode('utf-8')
            return False
        except UnicodeDecodeError:
            # Check for binary patterns
            # Look at first 1024 bytes for null bytes or high number of non-ASCII chars
            sample = content[:1024]
            null_count = sample.count(b'\x00')
            non_ascii = sum(1 for b in sample if b > 0x7F)
            
            # If more than 30% non-ASCII or contains null bytes, likely binary
            return (null_count > 0) or (non_ascii / len(sample) > 0.3)

    @staticmethod
    def is_xml_content(content: Union[str, bytes]) -> bool:
        """Check if content is valid XML."""
        try:
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            # Try to parse the XML
            ET.fromstring(content)
            return True
        except Exception:
            return False

    @staticmethod
    def is_svg_content(content: Union[str, bytes]) -> bool:
        """Check if content is SVG."""
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        # First check if it's valid XML
        if not ContentTypeInterpreter.is_xml_content(content):
            return False
        
        content = content.strip().lower()
        
        # Check for SVG namespace or SVG root element
        return (
            'xmlns="http://www.w3.org/2000/svg"' in content or
            'xmlns:svg="http://www.w3.org/2000/svg"' in content or
            content.startswith('<?xml') and '<svg' in content[:1000] or
            content.startswith('<svg')
        )

    @staticmethod
    def validate_content(content: Any) -> bool:
        """Validate content type."""
        return isinstance(content, (str, bytes, bytearray))
