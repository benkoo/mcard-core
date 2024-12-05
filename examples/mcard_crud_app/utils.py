"""Utility functions for MCard CRUD application."""
import logging
import math
from typing import Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class RequestParamHandler:
    """Centralized handler for request parameter parsing and validation."""
    
    @staticmethod
    def safe_int_convert(
        param: Any, 
        default: int = 1, 
        min_value: int = 1, 
        max_value: Optional[int] = None
    ) -> int:
        """
        Safely convert a parameter to an integer with extensive error handling.
        
        Args:
            param: The parameter to convert
            default: Default value if conversion fails
            min_value: Minimum allowed value
            max_value: Maximum allowed value (optional)
        
        Returns:
            Converted integer within specified bounds
        """
        if param is None:
            return default
        
        try:
            # Convert to string and strip whitespace
            str_param = str(param).strip()
            
            # Remove commas and other non-numeric characters
            str_param = ''.join(char for char in str_param if char.isdigit() or char == '.')
            
            # Convert to float first to handle decimal inputs
            float_value = float(str_param)
            
            # Convert to integer
            int_value = int(float_value)
            
            # Apply bounds
            int_value = max(min_value, int_value)
            
            if max_value is not None:
                int_value = min(int_value, max_value)
            
            return int_value
        
        except (ValueError, TypeError) as e:
            # Log the error for debugging
            logger.error(f"Integer conversion error: {e}")
            return default
    
    @staticmethod
    def parse_int_param(
        param: Any, 
        default: int = 1, 
        min_value: int = 1, 
        max_value: Optional[int] = None,
        param_name: str = 'parameter'
    ) -> int:
        """
        Parse an integer parameter with comprehensive error handling.
        
        Args:
            param: Input parameter to parse
            default: Default value if parsing fails
            min_value: Minimum allowed value
            max_value: Maximum allowed value (optional)
            param_name: Name of the parameter for logging
        
        Returns:
            Validated integer value
        """
        # Log the raw input for debugging
        logger.info(f"Parsing {param_name}: {param} (type: {type(param)})")
        
        # Use safe conversion method
        result = RequestParamHandler.safe_int_convert(
            param, 
            default=default, 
            min_value=min_value, 
            max_value=max_value
        )
        
        logger.info(f"Parsed {param_name}: {result}")
        return result
    
    @staticmethod
    def paginate(
        items: list, 
        page: int = 1, 
        per_page: int = 12
    ) -> Tuple[list, int, int]:
        """
        Paginate a list of items.
        
        Args:
            items: List of items to paginate
            page: Current page number
            per_page: Number of items per page
        
        Returns:
            Tuple of (current_page_items, total_pages, total_items)
        """
        # Ensure page and per_page are valid integers
        page = max(1, int(page))
        per_page = max(1, int(per_page))
        
        total_items = len(items)
        total_pages = math.ceil(total_items / per_page)
        
        # Adjust page if out of bounds
        page = min(page, total_pages)
        
        # Calculate start and end indices
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        
        current_page_items = items[start_index:end_index]
        
        return current_page_items, total_pages, total_items
