"""Content analyzer implementation for analyzing MCard content."""
from typing import Optional, List, Dict, Union, Any
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import mimetypes
import filetype
import requests
from langdetect import detect_langs
from mcard import MCard
import os

@dataclass
class LanguageInfo:
    """Information about detected language."""
    lang: str
    prob: float

@dataclass
class MCardInfo:
    """Basic information about an MCard."""
    content_hash: str
    time_claimed: datetime

@dataclass
class AnalyzerInfo:
    """Information about an analyzer."""
    host: str
    model: str

@dataclass
class AnalysisResult:
    """Results of content analysis."""
    title: str
    mime_type: str
    languages: List[LanguageInfo]
    summary: str
    mcard: MCardInfo
    authors: Dict[str, AnalyzerInfo]

class AnalyzerConfig:
    """Configuration for the content analyzer."""
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        ollama_model: str = "llava"
    ):
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'AnalyzerConfig':
        """Create config from environment variables.
        
        Args:
            env_file: Optional path to .env file to load
            
        Returns:
            AnalyzerConfig initialized with values from environment
        """
        from mcard import config
        
        # Load environment if env_file provided
        if env_file:
            config.load_config(env_file)
            
        # Get Ollama config from environment
        return cls(
            ollama_host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
            ollama_model=os.getenv('OLLAMA_MODEL', 'llava')
        )

class MimeTypeAnalyzer:
    """Analyzer for detecting MIME types without requiring external binaries."""
    
    def __init__(self):
        """Initialize the MIME type analyzer."""
        mimetypes.init()
        # Add additional MIME types not in the default database
        mimetypes.add_type('application/x-empty', '.empty')
        mimetypes.add_type('text/markdown', '.md')
        mimetypes.add_type('text/markdown', '.markdown')

    def _guess_from_content(self, content: bytes) -> Optional[str]:
        """Guess MIME type from content using filetype library."""
        kind = filetype.guess(content)
        return kind.mime if kind else None

    def _guess_from_content_heuristics(self, content: bytes) -> str:
        """Use simple heuristics to guess MIME type from content."""
        # Try to decode as UTF-8 text
        try:
            content.decode('utf-8')
            return 'text/plain'
        except UnicodeDecodeError:
            pass
        
        # Check for common file signatures
        if content.startswith(b'%PDF'):
            return 'application/pdf'
        elif content.startswith(b'\x89PNG\r\n'):
            return 'image/png'
        elif content.startswith(b'\xFF\xD8\xFF'):
            return 'image/jpeg'
        
        # Default to binary
        return 'application/octet-stream'

    def analyze(self, content: Union[str, bytes], filename: Optional[str] = None) -> str:
        """Detect MIME type of content using multiple methods.
        
        Args:
            content: The content to analyze
            filename: Optional filename to help with MIME type detection
            
        Returns:
            Detected MIME type as string
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
            
        # Empty content check
        if not content:
            return 'application/x-empty'
            
        # Try to detect from content first using filetype
        if len(content) >= 8:  # filetype needs at least 8 bytes
            mime_type = self._guess_from_content(content)
            if mime_type:
                return mime_type
                
        # If filename is provided, try to guess from extension
        if filename:
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                return mime_type
                
        # Fall back to basic heuristics
        return self._guess_from_content_heuristics(content)

class LanguageAnalyzer:
    """Analyzer for detecting text languages."""
    
    def analyze(self, content: Union[str, bytes]) -> List[LanguageInfo]:
        """Detect languages in text content."""
        if isinstance(content, bytes):
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                return []
        else:
            text = content

        try:
            langs = detect_langs(text)
            return [LanguageInfo(lang=l.lang, prob=l.prob) for l in langs]
        except:
            return []

class SummaryAnalyzer:
    """Analyzer for generating content summaries using Ollama."""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "llava"):
        self.host = host
        self.model = model
        
    def analyze(self, content: Union[str, bytes], mime_type: str, primary_lang: Optional[str] = None) -> str:
        """Generate a summary of the content."""
        if isinstance(content, bytes):
            try:
                text = content.decode('utf-8', errors='ignore')
            except:
                text = "<binary content>"
        else:
            text = content
            
        # Prepare prompt based on content type and language
        if mime_type.startswith('text/'):
            prompt = f"Please summarize the following text"
            if primary_lang and primary_lang != 'en':
                prompt += f" (in {primary_lang})"
            prompt += ":\n\n" + text
        else:
            prompt = f"This is {mime_type} content. Please describe what you see."
            
        # Call Ollama API
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
            return response.json()['response'].strip()
        except:
            return "Failed to generate summary"

class ContentAnalyzer:
    """Main content analyzer class that coordinates different analyzers."""
    
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        """Initialize content analyzer with configuration."""
        self.config = config or AnalyzerConfig()
        self.mime_analyzer = MimeTypeAnalyzer()
        self.lang_analyzer = LanguageAnalyzer()
        self.summary_analyzer = SummaryAnalyzer(
            host=self.config.ollama_host,
            model=self.config.ollama_model
        )

    def _generate_title(self, content: Union[bytes, str], mime_type: str, primary_lang: Optional[str] = None) -> str:
        """Generate a title for the content using Ollama."""
        analyzer = SummaryAnalyzer(host=self.config.ollama_host, model=self.config.ollama_model)
        if isinstance(content, bytes):
            try:
                text = content.decode('utf-8', errors='ignore')
            except:
                text = "<binary content>"
        else:
            text = content

        # Prepare prompt based on content type
        if mime_type.startswith('text/'):
            prompt = "Generate a short, descriptive title (max 10 words) for this text:\n\n" + text
        else:
            prompt = f"Generate a short, descriptive title (max 10 words) for this {mime_type} content."

        try:
            response = requests.post(
                f"{self.config.ollama_host}/api/generate",
                json={
                    "model": self.config.ollama_model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()['response'].strip()
        except:
            return "Untitled Content"

    def analyze_card(self, card: MCard) -> AnalysisResult:
        """Analyze a single MCard and return results."""
        # Get MIME type
        mime_type = self.mime_analyzer.analyze(card.content)
        
        # Detect languages if text content
        languages = []
        primary_lang = None
        if mime_type.startswith('text/'):
            languages = self.lang_analyzer.analyze(card.content)
            if languages:
                primary_lang = max(languages, key=lambda x: x.prob).lang
        
        # Generate title and summary
        title = self._generate_title(card.content, mime_type, primary_lang)
        summary = self.summary_analyzer.analyze(card.content, mime_type, primary_lang)
        
        # Create result
        return AnalysisResult(
            title=title,
            mime_type=mime_type,
            languages=languages,
            summary=summary,
            mcard=MCardInfo(
                content_hash=card.content_hash,
                time_claimed=card.time_claimed
            ),
            authors={
                'title': AnalyzerInfo(
                    host=self.config.ollama_host,
                    model=self.config.ollama_model
                ),
                'summary': AnalyzerInfo(
                    host=self.config.ollama_host,
                    model=self.config.ollama_model
                )
            }
        )

    def analyze_cards(self, cards: List[MCard], max_workers: int = 4) -> List[AnalysisResult]:
        """Analyze multiple cards in parallel."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(self.analyze_card, cards))

    def save_results(self, results: Union[AnalysisResult, List[AnalysisResult]], 
                    output_path: Optional[Path] = None):
        """Save analysis results to a JSON file."""
        if output_path is None:
            output_path = Path('analysis_results.json')
            
        if isinstance(results, AnalysisResult):
            results = [results]
            
        class ResultEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (AnalysisResult, LanguageInfo, MCardInfo, AnalyzerInfo)):
                    return obj.__dict__
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
            
        with open(output_path, 'w') as f:
            json.dump(results, f, cls=ResultEncoder, indent=2)

    def generate_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """Generate a summary of analysis results."""
        mime_types = {}
        languages = {}
        total_cards = len(results)
        
        for result in results:
            # Count MIME types
            mime_types[result.mime_type] = mime_types.get(result.mime_type, 0) + 1
            
            # Count languages
            for lang in result.languages:
                languages[lang.lang] = languages.get(lang.lang, 0) + 1
                
        return {
            'total_cards': total_cards,
            'mime_types': mime_types,
            'languages': languages
        }

class CardGenerator:
    """Utility class for generating test cards with various content types."""
    
    @staticmethod
    def create_text_card(content: str) -> MCard:
        """Create a card with text content."""
        return MCard(content=content)
    
    @staticmethod
    def create_binary_card(content: bytes) -> MCard:
        """Create a card with binary content."""
        return MCard(content=content)
    
    @classmethod
    def create_spanish_card(cls) -> MCard:
        """Create a card with Spanish content."""
        content = """
        El sol brilla intensamente en el cielo azul. Las aves cantan melodías
        dulces mientras vuelan entre los árboles. El viento sopla suavemente,
        moviendo las hojas en un baile natural. Es un día perfecto para estar
        al aire libre y disfrutar de la naturaleza.
        """
        return cls.create_text_card(content)
    
    @classmethod
    def create_french_technical_card(cls) -> MCard:
        """Create a card with French technical content."""
        content = """
        Le langage Python est un langage de programmation polyvalent qui prend
        en charge plusieurs paradigmes de programmation. Il est particulièrement
        apprécié pour sa syntaxe claire et sa vaste bibliothèque standard.
        La gestion automatique de la mémoire facilite le développement.
        """
        return cls.create_text_card(content)
    
    @classmethod
    def create_json_card(cls) -> MCard:
        """Create a card with JSON content."""
        content = json.dumps({
            "name": "Test Card",
            "type": "JSON",
            "properties": {
                "version": 1,
                "format": "application/json"
            }
        }, indent=2)
        return cls.create_text_card(content)
    
    @classmethod
    def create_test_suite(cls) -> List[MCard]:
        """Create a suite of test cards with various content types."""
        return [
            cls.create_spanish_card(),
            cls.create_french_technical_card(),
            cls.create_json_card()
        ]
