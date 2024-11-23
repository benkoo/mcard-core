"""Card generation utilities for testing and examples."""
from typing import Optional, Dict, Any
from mcard import MCard

class CardGenerator:
    """Utility class for generating test cards with various content types."""
    
    @staticmethod
    def create_text_card(content: str, metadata: Optional[Dict[str, Any]] = None) -> MCard:
        """Create a card with text content."""
        return MCard(content=content)
    
    @staticmethod
    def create_binary_card(content: bytes, metadata: Optional[Dict[str, Any]] = None) -> MCard:
        """Create a card with binary content."""
        return MCard(content=content)
    
    @classmethod
    def create_spanish_card(cls) -> MCard:
        """Create a card with Spanish content."""
        content = """
        La inteligencia artificial (IA) es la simulación de procesos de inteligencia 
        humana por parte de máquinas, especialmente sistemas informáticos. Estos 
        procesos incluyen el aprendizaje (la adquisición de información y reglas 
        para el uso de la información), el razonamiento (usando las reglas para 
        llegar a conclusiones aproximadas o definitivas) y la autocorrección.
        """
        return cls.create_text_card(content)
    
    @classmethod
    def create_french_technical_card(cls) -> MCard:
        """Create a card with French technical content."""
        content = """
        L'apprentissage profond (deep learning) est un type d'intelligence 
        artificielle dérivé du machine learning (apprentissage automatique) où 
        la machine est capable d'apprendre par elle-même, contrairement à une 
        programmation explicite basée sur un jeu de règles.
        """
        return cls.create_text_card(content)
    
    @classmethod
    def create_json_card(cls) -> MCard:
        """Create a card with JSON content."""
        content = """{
            "name": "Test Card",
            "type": "JSON Example",
            "properties": {
                "version": "1.0",
                "author": "MCard Generator",
                "tags": ["test", "example", "json"]
            }
        }"""
        return cls.create_text_card(content)
    
    @classmethod
    def create_test_suite(cls) -> list[MCard]:
        """Create a suite of test cards with various content types."""
        return [
            cls.create_spanish_card(),
            cls.create_french_technical_card(),
            cls.create_json_card(),
            cls.create_text_card("Hello, World!"),
            cls.create_binary_card(b'\x00\x01\x02\x03')
        ]
