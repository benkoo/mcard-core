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
                # Validate XML structure
                try:
                    ET.fromstring(content)
                    return 'application/xml'
                except ET.ParseError:
                    pass
            except:
                pass
        
        # Try to detect JSON
        try:
            text_content = content.decode('utf-8', errors='ignore')
            text_content = text_content.strip()
            if text_content.startswith('{') and text_content.endswith('}'):
                try:
                    json.loads(text_content)
                    return 'application/json'
                except json.JSONDecodeError:
                    pass
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
                try:
                    ET.fromstring(content_bytes)
                    # Check if it's specifically an SVG
                    if ContentTypeInterpreter.is_svg_content(content):
                        return 'image/svg+xml', 'svg'
                    # Generic XML
                    return 'application/xml', 'xml'
                except ET.ParseError:
                    pass
            except Exception:
                pass
            
            # Default to text/plain for strings
            return 'text/plain', 'txt'
        
        elif isinstance(content, bytes):
            # First try to detect XML content
            if content.startswith(b'<?xml') or content.lstrip(b' \t\n\r').startswith(b'<'):
                try:
                    text_content = content.decode('utf-8')
                    try:
                        ET.fromstring(content)
                        if ContentTypeInterpreter.is_svg_content(text_content):
                            return 'image/svg+xml', 'svg'
                        return 'application/xml', 'xml'
                    except ET.ParseError:
                        # Invalid XML should be treated as text
                        return 'text/plain', 'txt'
                except UnicodeDecodeError:
                    pass

            # Then check for binary signatures at the start
            for signature, mime_type in ContentTypeInterpreter.SIGNATURES.items():
                if content.startswith(signature):
                    return mime_type, ContentTypeInterpreter.get_extension(mime_type)

            # If no specific binary format detected, check for text formats
            try:
                text_content = content.decode('utf-8')
                text_content = text_content.strip()
                
                # Check for JSON
                if text_content.startswith('{') and text_content.endswith('}'):
                    try:
                        # Check for comments
                        lines = text_content.split('\n')
                        if any(line.strip().startswith('//') for line in lines):
                            return 'text/plain', 'txt'
                        json.loads(text_content)
                        return 'application/json', 'json'
                    except json.JSONDecodeError:
                        return 'text/plain', 'txt'
                
                # Default to text/plain for decodeable content
                return 'text/plain', 'txt'
            except UnicodeDecodeError:
                pass
            
            # Check for mixed content
            if content.startswith(b'<?xml'):
                return 'application/xml', 'xml'
            
            return 'application/octet-stream', ''

        raise ValidationError("Content must be string or bytes")

    def validate_content(self, content: Union[str, bytes]) -> bool:
        """Validate content based on its detected type."""
        if not content:
            raise ValidationError("Empty content")

        try:
            mime_type, _ = self.detect_content_type(content)

            # For text content, try to validate as JSON or XML first
            if mime_type == 'text/plain':
                if isinstance(content, bytes):
                    text_content = content.decode('utf-8')
                else:
                    text_content = content

                # Try JSON first
                text_content = text_content.strip()
                if text_content.startswith('{') and text_content.endswith('}'):
                    try:
                        # Check for comments
                        lines = text_content.split('\n')
                        if any(line.strip().startswith('//') for line in lines):
                            raise ValidationError("Invalid JSON content")
                        json.loads(text_content)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        raise ValidationError("Invalid JSON content")

                # Then try XML
                elif (text_content.startswith('<?xml') or 
                      text_content.lstrip().startswith('<')):
                    try:
                        ET.fromstring(text_content.encode('utf-8'))
                    except (ET.ParseError, UnicodeDecodeError):
                        raise ValidationError("Invalid XML content")

                # Ensure it's valid UTF-8
                try:
                    if isinstance(content, bytes):
                        content.decode('utf-8')
                except UnicodeDecodeError:
                    raise ValidationError("Invalid text content: not UTF-8 encoded")

            # Handle text-based content types
            elif mime_type == 'application/json':
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                try:
                    # Check for comments before attempting to parse
                    lines = content.split('\n')
                    if any(line.strip().startswith('//') for line in lines):
                        raise ValidationError("Invalid JSON content")
                    json.loads(content)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    raise ValidationError("Invalid JSON content")

            elif mime_type == 'application/xml' or mime_type == 'image/svg+xml':
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                try:
                    ET.fromstring(content)
                except (ET.ParseError, UnicodeDecodeError):
                    raise ValidationError("Invalid XML content")
                # Check for mixed content (XML + binary)
                if isinstance(content, str):
                    content = content.encode('utf-8')
                for signature in ContentTypeInterpreter.SIGNATURES:
                    if signature in content and not content.startswith(signature):
                        raise ValidationError("Invalid XML content")

            # Handle binary content types
            elif mime_type.startswith('image/'):
                # Basic validation for image formats
                if mime_type == 'image/png' and len(content) <= 8:  # PNG header is 8 bytes
                    raise ValidationError("Invalid content: truncated PNG file")
                elif mime_type == 'image/jpeg' and len(content) <= 3:  # JPEG header is 3 bytes
                    raise ValidationError("Invalid content: truncated JPEG file")
                elif mime_type == 'image/gif' and len(content) <= 6:  # GIF header is 6 bytes
                    raise ValidationError("Invalid content: truncated GIF file")

            elif mime_type == 'application/pdf':
                if not content.startswith(b'%PDF-'):
                    raise ValidationError("Invalid PDF content")

            elif mime_type == 'application/zip':
                if len(content) <= 4:  # ZIP header is 4 bytes
                    raise ValidationError("Invalid ZIP content")

            return True

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Invalid content: {str(e)}")

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
            # Check for binary patterns
            # Look at first 1024 bytes for null bytes or high number of non-ASCII chars
            sample = content[:1024]
            if not sample:  # Handle empty content
                return False
                
            null_count = sample.count(b'\x00')
            non_ascii = sum(1 for b in sample if b > 0x7F)
            
            # If more than 30% non-ASCII or contains null bytes, likely binary
            return (null_count > 0) or (non_ascii / len(sample) > 0.3)
        except UnicodeDecodeError:
            return True

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
        
        try:
            # Parse XML and check for SVG namespace
            tree = ET.fromstring(content)
            return (
                tree.tag == 'svg' or
                tree.tag.endswith('}svg') or
                any(attr.endswith('xmlns') and 'svg' in value
                    for attr, value in tree.attrib.items())
            )
        except Exception:
            return False

    @staticmethod
    def get_extension(mime_type: str) -> str:
        """Get file extension from MIME type."""
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
        }.get(mime_type) or mimetypes.guess_extension(mime_type, strict=False)

        if extension and extension.startswith('.'):
            extension = extension[1:]
        
        return extension or ''

    @staticmethod
    def get_default_extension(mime_type: str) -> str:
        """
        Return the default file extension for a given MIME type.
        """
        mime_to_extension = {
            'application/pdf': 'pdf',
            'text/plain': 'txt',
            'image/png': 'png',
            'image/jpeg': 'jpg',
            'video/quicktime': 'mov',
            'application/x-tex': 'tex',
            'application/3d-obj': 'obj',
            'image/svg+xml': 'svg',
            'text/x-mermaid': 'mmd',
            'image/vnd.djvu': 'djv',
            'image/vnd.dxf': 'dxf',
            # Add more mappings as needed
        }
        return mime_to_extension.get(mime_type, '')
