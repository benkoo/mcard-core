"""
Content type detection and interpretation module for MCard CRUD application.
Provides functionality to detect MIME types and file extensions based on content signatures.
"""

import os
import json
import mimetypes
from typing import Optional, Dict, Any, List, Tuple
from .core import MCard
from urllib.parse import quote
import re

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

        # Check for SVG content first
        if cls.is_svg_content(content):
            return 'image/svg+xml', '.svg'

        # Then check for binary file signatures
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
    def is_svg_content(cls, content) -> bool:
        """
        Check if the content is SVG by looking for SVG markers.
        
        Args:
            content: The content to analyze (bytes or str)
            
        Returns:
            bool: True if content is SVG, False otherwise
        """
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                return False
        
        content = content.strip().lower()
        return (content.startswith('<?xml') or content.startswith('<svg')) and '</svg>' in content

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

    @classmethod
    def prepare_download_response(cls, content: bytes, content_hash: str, filename_prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare download response headers and filename for content.
        
        Args:
            content: The binary content to prepare for download
            content_hash: The hash of the content
            filename_prefix: Optional prefix for the filename (defaults to first 8 chars of content_hash)
            
        Returns:
            Dictionary containing:
                - mime_type: The detected MIME type
                - filename: The suggested filename
                - headers: Dict of headers for the response
        """
        mime_type, extension = cls.detect_content_type(content)
        
        # Remove leading dot from extension if present
        extension = extension.lstrip('.') if extension else ''
        
        # Use provided prefix or default to content hash prefix
        prefix = filename_prefix or content_hash[:8]
        filename = f"{prefix}.{extension}" if extension else prefix
        quoted_filename = quote(filename)
        
        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'attachment; filename="{quoted_filename}"'
        }
        
        return {
            'mime_type': mime_type,
            'filename': filename,
            'headers': headers
        }

    @classmethod
    def is_image_content(cls, content_type: str) -> bool:
        """Check if the content type is an image format.
        
        Args:
            content_type: MIME type of the content
            
        Returns:
            bool: True if content is an image type
        """
        return content_type.startswith('image/')

    @classmethod
    def check_duplicate_content(cls, storage, content):
        """Check if content already exists in storage by comparing content hashes.
        
        Args:
            storage: Storage instance to check against
            content: Content to check for duplicates
            
        Returns:
            dict: Dictionary with 'found' boolean and 'hash' if found
        """
        try:
            print("[ContentTypeInterpreter] Starting duplicate content check")
            print(f"[ContentTypeInterpreter] Content type: {type(content)}")
            print(f"[ContentTypeInterpreter] Content length: {len(content)}")
            
            # Create an MCard to get the content hash
            new_card = MCard(content=content)
            print(f"[ContentTypeInterpreter] Generated hash for new content: {new_card.content_hash}")
            
            # Try to get card with same hash from storage
            existing_card = storage.get(new_card.content_hash)
            print(f"[ContentTypeInterpreter] Existing card lookup result: {existing_card is not None}")
            
            if existing_card:
                print(f"[ContentTypeInterpreter] Found existing card with matching hash: {existing_card.content_hash}")
                return {"found": True, "hash": existing_card.content_hash}
            
            print("[ContentTypeInterpreter] No matching hash found")
            return {"found": False}
            
        except Exception as e:
            print(f"[ContentTypeInterpreter] Error in check_duplicate_content: {str(e)}")
            print(f"[ContentTypeInterpreter] Error type: {type(e)}")
            import traceback
            print(f"[ContentTypeInterpreter] Traceback: {traceback.format_exc()}")
            return {"found": False}
