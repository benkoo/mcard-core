"""Content analyzers for different aspects of MCard content."""
from typing import List, Optional
import magic
import langdetect
import requests
from abc import ABC, abstractmethod
from mcard import MCard
from .models import LanguageInfo

class BaseAnalyzer(ABC):
    """Base class for content analyzers."""
    
    @abstractmethod
    def analyze(self, content: bytes | str) -> any:
        """Analyze the content and return results."""
        pass

class MimeTypeAnalyzer(BaseAnalyzer):
    """Analyzer for MIME type detection."""
    
    def __init__(self):
        self.mime = magic.Magic(mime=True)
    
    def analyze(self, content: bytes | str) -> str:
        """Determine the MIME type of the content."""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return self.mime.from_buffer(content)

class LanguageAnalyzer(BaseAnalyzer):
    """Analyzer for language detection."""
    
    def analyze(self, content: bytes | str) -> List[LanguageInfo]:
        """Detect languages in the content."""
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                return []
        
        try:
            langs = langdetect.detect_langs(content)
            return [LanguageInfo(lang=str(lang.lang), prob=lang.prob) for lang in langs]
        except langdetect.lang_detect_exception.LangDetectException:
            return []

class SummaryAnalyzer(BaseAnalyzer):
    """Analyzer for content summarization using Ollama."""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "llava"):
        self.host = host
        self.model = model
    
    def analyze(self, content: bytes | str, mime_type: str, primary_lang: Optional[str] = None) -> str:
        """Generate a summary of the content."""
        # Prepare the prompt based on content type and language
        if primary_lang:
            lang_prompt = f" Please respond in {primary_lang}."
        else:
            lang_prompt = ""
        
        if mime_type.startswith('image/'):
            prompt = f"Please describe this image.{lang_prompt}"
        else:
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            prompt = f"Please summarize this content: {content[:1000]}{lang_prompt}"

        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json().get('response', 'No summary available')
        except requests.exceptions.RequestException as e:
            return f"Error generating summary: {str(e)}"
