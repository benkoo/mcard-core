"""
Content type detection and interpretation module for MCard CRUD application.
Provides functionality to detect MIME types and file extensions based on content signatures.
"""

import json
import re
from typing import Tuple, Optional

class ContentTypeInterpreter:
    """Handles content type detection and interpretation for various file formats."""

    # File signatures for different content types
    SIGNATURES = {
        b'\x89PNG\r\n\x1a\n': ('image/png', 'png'),
        b'\xff\xd8\xff': ('image/jpeg', 'jpg'),
        b'GIF87a': ('image/gif', 'gif'),
        b'GIF89a': ('image/gif', 'gif'),
        b'RIFF': ('image/webp', 'webp'),  # WEBP
        b'II*\x00': ('image/tiff', 'tiff'),  # TIFF
        b'MM\x00*': ('image/tiff', 'tiff'),  # TIFF
        b'PK\x03\x04': ('application/zip', 'zip'),
        b'%PDF': ('application/pdf', 'pdf'),
        b'\x50\x4B\x03\x04\x14\x00\x06\x00': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx'),
        b'\x50\x4B\x03\x04\x14\x00\x08\x00': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx'),
    }

    @classmethod
    def detect_content_type(cls, content: bytes) -> Tuple[str, Optional[str]]:
        """
        Detect the MIME type and file extension of content based on its signature and content analysis.
        
        Args:
            content: The binary content to analyze
            
        Returns:
            Tuple containing (mime_type, file_extension)
        """
        # Handle non-bytes input
        if not isinstance(content, bytes):
            content = str(content).encode('utf-8')

        # First check for binary file signatures
        for signature, (mime_type, extension) in cls.SIGNATURES.items():
            if content.startswith(signature):
                return mime_type, f".{extension}"

        # Try to decode as text
        try:
            text_content = content.decode('utf-8')
            
            # Check for JSON
            try:
                json.loads(text_content)
                return 'application/json', '.json'
            except json.JSONDecodeError:
                pass

            # Check for XML by looking for XML declaration or root element
            if text_content.lstrip().startswith('<?xml') or re.search(r'<\?xml\s+version=', text_content):
                return 'application/xml', '.xml'

            # Check for HTML
            if re.search(r'<!DOCTYPE\s+html|<html\s*>', text_content, re.IGNORECASE):
                return 'text/html', '.html'

            # Check for PEM certificates
            if '-----BEGIN CERTIFICATE-----' in text_content:
                return 'application/x-pem-file', '.pem'

            # Default to plain text if nothing else matches
            return 'text/plain', '.txt'

        except UnicodeDecodeError:
            # If content can't be decoded as text, it's binary
            return 'application/octet-stream', None

    @classmethod
    def get_content_size_str(cls, size_in_bytes: int) -> str:
        """
        Convert size in bytes to human-readable format.
        
        Args:
            size_in_bytes: Size in bytes
            
        Returns:
            Human-readable size string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024:
                if unit == 'B':
                    return f"{size_in_bytes} {unit}"
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.1f} TB"
