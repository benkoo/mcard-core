"""
Configuration models for MCard.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field

# Simple literal type for hash algorithms
HashAlgorithm = Literal["sha256", "sha512", "sha1", "md5", "custom"]

class DatabaseSettings(BaseModel):
    """Database configuration."""
    db_path: str = Field(description="Path to the database file")
    data_source: Optional[str] = Field(None, description="Optional data source identifier")
    pool_size: int = Field(default=5, description="Connection pool size")
    timeout: float = Field(default=30.0, description="Database operation timeout in seconds")

class HashingSettings(BaseModel):
    """Hashing configuration."""
    algorithm: HashAlgorithm = Field(
        default="sha256",
        description="Hash function to use"
    )
    custom_module: Optional[str] = Field(None, description="Custom hash function module")
    custom_function: Optional[str] = Field(None, description="Custom hash function name")
    custom_hash_length: Optional[int] = Field(None, description="Expected length of custom hash")

class AppSettings(BaseModel):
    """Application settings."""
    database: DatabaseSettings
    hashing: HashingSettings = Field(default_factory=HashingSettings)
