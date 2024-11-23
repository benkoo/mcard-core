"""Configuration module for MCard."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parents[1]

def load_config(env_path: Optional[Path] = None) -> None:
    """Load environment variables from .env file."""
    if env_path is None:
        env_path = get_project_root() / ".env"
    load_dotenv(env_path)

def get_data_source() -> str:
    """Get the data source directory path."""
    data_source = os.getenv("MCARD_DATA_SOURCE")
    if not data_source:
        raise ValueError("MCARD_DATA_SOURCE not set in environment")
    return str(get_project_root() / data_source)

def get_db_path(test: bool = False) -> str:
    """Get the database path."""
    env_var = "MCARD_TEST_DB" if test else "MCARD_DB"
    db_path = os.getenv(env_var)
    if not db_path:
        raise ValueError(f"{env_var} not set in environment")
    
    # Convert to absolute path and ensure directory exists
    db_path = get_project_root() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)
