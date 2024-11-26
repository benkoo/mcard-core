"""
MCard Core: A content-addressable data wrapper library.
"""

from .core import MCard, get_now_with_located_zone
from .storage import MCardStorage
from .content_type_interpreter import ContentTypeInterpreter

__version__ = "0.1.0"
__all__ = ["MCard", "get_now_with_located_zone", "MCardStorage", "ContentTypeInterpreter"]
