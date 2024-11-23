"""Data models for the content interpreter."""
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class LanguageInfo(BaseModel):
    """Information about a detected language."""
    lang: str
    prob: float

class MCardInfo(BaseModel):
    """Basic information about the analyzed MCard."""
    content_hash: str
    time_claimed: datetime

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        d['time_claimed'] = d['time_claimed'].isoformat()
        return d

class AnalyzerInfo(BaseModel):
    """Information about the analyzer used."""
    host: str
    model: str

class AnalysisResult(BaseModel):
    """Result of content analysis."""
    title: str = Field(..., max_length=100)
    mime_type: str
    languages: List[LanguageInfo]
    summary: str
    mcard: MCardInfo
    authors: Dict[str, AnalyzerInfo] = Field(
        default_factory=dict,
        description="Dictionary of analyzers used, e.g., {'summary': {'host': 'http://...', 'model': 'llava'}}"
    )

    class Config:
        json_encoders = {
            bytes: lambda v: v.hex(),
            datetime: lambda v: v.isoformat()
        }
