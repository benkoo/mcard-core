"""Batch processing functionality for analyzing multiple cards."""
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from mcard import MCard
from .core import ContentInterpreter
from .config import InterpreterConfig
from .models import AnalysisResult

class BatchAnalyzer:
    """Handles batch analysis of multiple cards."""
    
    def __init__(self, config: Optional[InterpreterConfig] = None):
        self.config = config or InterpreterConfig()
        self.interpreter = ContentInterpreter(config)
    
    def analyze_cards(self, cards: List[MCard], max_workers: int = 4) -> List[AnalysisResult]:
        """Analyze multiple cards in parallel."""
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.interpreter.analyze_card, card) for card in cards]
            results = [future.result() for future in futures]
        return results
    
    def analyze_from_db(self, db_path: Optional[str] = None) -> List[AnalysisResult]:
        """Load and analyze cards from a database."""
        db_path = db_path or self.config.db_path
        if not db_path:
            raise ValueError("Database path not provided")
        
        # TODO: Implement proper database loading
        # For now, just use test cards
        from .generators import CardGenerator
        cards = CardGenerator().create_test_suite()
        return self.analyze_cards(cards)
    
    def save_results(self, results: List[AnalysisResult], output_path: Optional[Path] = None) -> None:
        """Save analysis results to a JSON file."""
        output_path = output_path or self.config.output_dir
        if not output_path:
            output_path = Path('analysis_results.json')
        elif output_path.is_dir():
            output_path = output_path / 'analysis_results.json'
            
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
            
        with open(output_path, 'w') as f:
            json.dump([result.dict() for result in results], f, indent=2, cls=DateTimeEncoder)
    
    def generate_summary(self, results: List[AnalysisResult]) -> Dict:
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
            'mime_type_distribution': {
                mime: {'count': count, 'percentage': (count/total_cards)*100}
                for mime, count in mime_types.items()
            },
            'language_distribution': {
                lang: {'count': count, 'percentage': (count/total_cards)*100}
                for lang, count in languages.items()
            }
        }
