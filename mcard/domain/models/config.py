"""
Configuration models for MCard.
"""
from typing import Optional, Annotated, ClassVar
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, validator, ConfigDict, root_validator, model_validator, ValidationError as PydanticValidationError
from enum import Enum
from pydantic_settings import BaseSettings
from mcard.domain.models.exceptions import ValidationError
from zoneinfo import ZoneInfo, available_timezones

class HashFunction(str, Enum):
    """Supported hash functions."""
    SHA256 = "sha256"
    SHA512 = "sha512"
    SHA1 = "sha1"
    MD5 = "md5"  # Note: MD5 is not cryptographically secure
    CUSTOM = "custom"

class DatabaseSettings(BaseModel):
    """Database configuration."""
    db_path: str = Field(..., env="MCARD_DB_PATH")
    pool_size: int = Field(5, env="MCARD_DB_POOL_SIZE")
    timeout: float = Field(30.0, env="MCARD_DB_TIMEOUT")
    test_db_path: str = Field("test.db", env="MCARD_TEST_DB_PATH")

class HashingSettings(BaseModel):
    """Hashing configuration."""
    algorithm: HashFunction = Field(HashFunction.SHA256, env="MCARD_HASH_ALGORITHM")
    custom_module: Optional[str] = Field(None, env="MCARD_CUSTOM_HASH_MODULE")
    custom_function: Optional[str] = Field(None, env="MCARD_CUSTOM_HASH_FUNCTION")
    custom_hash_length: Optional[int] = Field(None, env="MCARD_CUSTOM_HASH_LENGTH")

class TimeSettings(BaseModel):
    """Time-related settings."""
    # Valid strftime directives
    VALID_DIRECTIVES: ClassVar[set[str]] = {'%Y', '%y', '%I', '%H', '%V', '%c', '%G', '%u', '%a', '%f', '%x', '%B', '%j', '%p', '%A', '%d', '%w', '%Z', '%%', '%M', '%S', '%z', '%m', '%W', '%X', '%b', '%U'}
    
    # Standard format for database storage - YYYY-MM-DD HH:MM:SS.microseconds timezone
    DB_TIME_FORMAT: ClassVar[str] = "%Y-%m-%d %H:%M:%S.%f %z"

    timezone: Optional[str] = None
    time_format: str = DB_TIME_FORMAT  # Default to database format
    date_format: str = "%Y-%m-%d"
    use_utc: bool = False

    model_config = ConfigDict(validate_assignment=True)

    @classmethod
    def _validate_format(cls, fmt: str) -> None:
        """Validate a format string by checking each directive."""
        i = 0
        while i < len(fmt):
            if fmt[i] == '%':
                if i + 1 >= len(fmt):
                    raise ValidationError(f"Invalid format string: {fmt} (incomplete directive)")
                
                # Check for two-character directive
                directive = fmt[i:i+2]
                if directive not in cls.VALID_DIRECTIVES:
                    raise ValidationError(f"Invalid format string: {fmt} (invalid directive {directive})")
                i += 2
            else:
                # Allow only specific separator characters
                if not fmt[i].isspace() and fmt[i] not in {'-', '/', ' '}:
                    raise ValidationError(f"Invalid format string: {fmt} (invalid character: {fmt[i]})")
                i += 1

        # Also try to use it with a sample datetime to catch other issues
        try:
            sample_dt = datetime.now(ZoneInfo("UTC"))
            sample_dt.strftime(fmt)
        except Exception as e:
            raise ValidationError(f"Invalid format string: {fmt} ({str(e)})")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        """Validate timezone string."""
        if v is not None:
            try:
                if v != "UTC":
                    ZoneInfo(v)  # This will raise ZoneInfoNotFoundError if invalid
            except Exception as e:
                raise ValidationError(f"Invalid timezone: {v}")
        return v

    @field_validator("time_format", mode="before")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format string."""
        if v != cls.DB_TIME_FORMAT:
            raise ValidationError(
                f"Time format must be '{cls.DB_TIME_FORMAT}' for database storage. "
                "This ensures microsecond precision and timezone information is preserved."
            )
        return v

    @field_validator("date_format", mode="before")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format string."""
        if not v:
            raise ValidationError("Date format cannot be empty")

        try:
            # First validate that we only have valid characters
            i = 0
            has_date_component = False
            while i < len(v):
                if v[i] == '%':
                    if i + 1 >= len(v):
                        raise ValidationError(f"Invalid format string: {v} (incomplete directive)")
                    
                    # Check for two-character directive
                    directive = v[i:i+2]
                    if directive not in {"%Y", "%m", "%d", "%b", "%B", "%a", "%A"}:
                        raise ValidationError(f"Invalid format string: {v} (invalid directive {directive})")
                    
                    # Track if we have at least one date component
                    if directive in {"%Y", "%m", "%d"}:
                        has_date_component = True
                    
                    i += 2
                else:
                    # Allow only specific separator characters
                    if not v[i].isspace() and v[i] not in {'-', '/', ' '}:
                        raise ValidationError(f"Invalid format string: {v} (invalid character: {v[i]})")
                    i += 1

            if not has_date_component:
                raise ValidationError(f"Invalid format string: {v} (must contain at least one date component)")

            # Try to use it with a sample datetime to catch other issues
            try:
                sample_dt = datetime.now(ZoneInfo("UTC"))
                sample_dt.strftime(v)
            except ValueError as e:
                raise ValidationError(f"Invalid format string: {v} ({str(e)})")
            return v
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Invalid format string: {v} ({str(e)})")

    @model_validator(mode="after")
    def validate_all(self) -> 'TimeSettings':
        """Validate all fields after model initialization."""
        if self.timezone:
            self.validate_timezone(self.timezone)
        return self

class AppSettings(BaseSettings):
    """Application settings."""
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    hashing: HashingSettings = Field(default_factory=HashingSettings)
    time: TimeSettings = Field(default_factory=TimeSettings)

    class Config:
        """Pydantic configuration."""
        env_prefix = "MCARD_"
        env_nested_delimiter = "__"
