"""Core content interpreter implementation."""
from typing import Optional
from datetime import datetime
from mcard import MCard
from .config import InterpreterConfig
from .models import AnalysisResult, MCardInfo, AnalyzerInfo
from .analyzers import MimeTypeAnalyzer, LanguageAnalyzer, SummaryAnalyzer

class ContentInterpreter:
    """Main content interpreter class that coordinates different analyzers."""
    
    def __init__(self, config: Optional[InterpreterConfig] = None):
        self.config = config or InterpreterConfig()
        self.mime_analyzer = MimeTypeAnalyzer()
        self.lang_analyzer = LanguageAnalyzer()
        self.summary_analyzer = SummaryAnalyzer(
            host=self.config.ollama_host,
            model=self.config.ollama_model
        )
    
    def _generate_title(self, content: bytes | str, mime_type: str, primary_lang: Optional[str] = None) -> str:
        """Generate a title for the content using Ollama."""
        if isinstance(content, bytes):
            try:
                content_preview = content.decode('utf-8', errors='ignore')[:500]
            except:
                content_preview = "<binary content>"
        else:
            content_preview = content[:500]
            
        prompt = f"Generate a concise title (less than 100 characters) for this content: {content_preview}"
        if primary_lang:
            prompt += f" Please respond in {primary_lang}."
            
        try:
            response = self.summary_analyzer.analyze(content_preview, mime_type, primary_lang)
            # Ensure title is not too long
            title = response.split('\n')[0][:99]
            return title
        except:
            return "Untitled Content"
    
    def analyze_card(self, card: MCard) -> AnalysisResult:
        """Analyze a single MCard and return results."""
        content = card.content
        
        # Get MIME type
        mime_type = self.mime_analyzer.analyze(content)
        
        # Detect languages
        languages = self.lang_analyzer.analyze(content)
        
        # Get primary language if available
        primary_lang = languages[0].lang if languages else None
        
        # Generate title
        title = self._generate_title(content, mime_type, primary_lang)
        
        # Generate summary
        summary = self.summary_analyzer.analyze(content, mime_type, primary_lang)
        
        # Get MCard info
        mcard_info = MCardInfo(
            content_hash=card.content_hash,
            time_claimed=card.time_claimed
        )
        
        # Create analyzer info
        analyzer_info = {
            'summary_analyzer': AnalyzerInfo(
                host=self.config.ollama_host,
                model=self.config.ollama_model
            )
        }
        
        return AnalysisResult(
            title=title,
            mime_type=mime_type,
            languages=languages,
            summary=summary,
            mcard=mcard_info,
            authors=analyzer_info
        )
