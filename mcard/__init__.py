"""
MCard Core: A content-addressable data wrapper library.
"""

from .core import MCard, get_now_with_located_zone
from .storage import MCardStorage
from .collection import MCardCollection

__version__ = "0.1.0"
__all__ = ["MCard", "get_now_with_located_zone", "MCardStorage", "MCardCollection"]
