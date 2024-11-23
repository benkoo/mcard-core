"""
Content Interpreter for MCard content.
Analyzes content to determine mime type, language, and generates a summary using Ollama.
"""
import json
import mimetypes
import magic
import langdetect
from langdetect import detect_langs
from typing import List, Dict, Union, Optional
import requests
from mcard import MCard
import os
from pathlib import Path
from dotenv import load_dotenv

class ContentInterpreter:
    """Interprets MCard content and provides analysis."""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """
        Initialize the interpreter.
        
        Args:
            ollama_host: URL of the Ollama server
        """
        self.ollama_host = ollama_host
        # Initialize mime type detection
        self.mime = magic.Magic(mime=True)
        mimetypes.init()

    def _get_mime_type(self, content: Union[str, bytes]) -> str:
        """
        Determine the MIME type of the content.
        
        Args:
            content: The content to analyze
            
        Returns:
            str: The detected MIME type
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        return self.mime.from_buffer(content)

    def _detect_languages(self, text: str) -> List[Dict[str, float]]:
        """
        Detect possible languages in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List[Dict[str, float]]: List of detected languages with probabilities
        """
        try:
            langs = detect_langs(text)
            return [{"lang": str(lang.lang), "prob": lang.prob} for lang in langs]
        except langdetect.lang_detect_exception.LangDetectException:
            return []

    def _get_summary(self, content: Union[str, bytes], mime_type: str, primary_lang: Optional[str] = None) -> str:
        """
        Generate a summary of the content using Ollama's llava model.
        
        Args:
            content: Content to summarize
            mime_type: MIME type of the content
            primary_lang: Primary language to use for the summary
            
        Returns:
            str: Generated summary
        """
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

        # Call Ollama API
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": "llava",
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json().get('response', 'No summary available')
        except requests.exceptions.RequestException as e:
            return f"Error generating summary: {str(e)}"

    def interpret(self, mcard: MCard) -> Dict:
        """
        Interpret the content of an MCard.
        
        Args:
            mcard: The MCard to interpret
            
        Returns:
            Dict: Analysis results including mime type, languages, and summary
        """
        content = mcard.content
        
        # Get MIME type
        mime_type = self._get_mime_type(content)
        result = {"mime_type": mime_type}
        
        # Detect languages for text content
        if mime_type.startswith('text/') or mime_type == 'application/json':
            if isinstance(content, bytes):
                text_content = content.decode('utf-8', errors='ignore')
            else:
                text_content = content
            languages = self._detect_languages(text_content)
            result["languages"] = languages
            primary_lang = languages[0]["lang"] if languages else None
        else:
            result["languages"] = []
            primary_lang = None
        
        # Generate summary
        summary = self._get_summary(content, mime_type, primary_lang)
        result["summary"] = summary
        
        return result

def main():
    """Main function to demonstrate usage."""
    import sys
    if len(sys.argv) != 2:
        print("Usage: python app.py <content_hash>")
        sys.exit(1)
    
    from mcard import MCardStorage
    
    # Load environment variables and get database path
    load_dotenv()
    db_path = os.getenv('MCARD_DB', 'data/db/MCardStore.db')
    if not os.path.isabs(db_path):
        root_dir = Path(__file__).parent.parent.parent
        db_path = os.path.join(root_dir, db_path)
    
    # Initialize storage and get the card
    storage = MCardStorage(db_path)
    card = storage.get(sys.argv[1])
    
    if not card:
        print(f"No card found with hash: {sys.argv[1]}")
        sys.exit(1)
    
    # Interpret the content
    interpreter = ContentInterpreter()
    result = interpreter.interpret(card)
    
    # Print the result as JSON
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
