"""Configuration for the content interpreter."""
from typing import Optional
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os

class InterpreterConfig(BaseModel):
    """Configuration for the content interpreter."""
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llava"
    db_path: Optional[str] = None
    output_dir: Optional[Path] = None
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'InterpreterConfig':
        """Create configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
            
        db_path = os.getenv('MCARD_DB')
        if db_path and not os.path.isabs(db_path):
            root_dir = Path(__file__).parent.parent.parent.parent
            db_path = str(root_dir / db_path)
            
        return cls(
            ollama_host=os.getenv('OLLAMA_HOST', cls.__fields__['ollama_host'].default),
            ollama_model=os.getenv('OLLAMA_MODEL', cls.__fields__['ollama_model'].default),
            db_path=db_path,
            output_dir=Path(os.getenv('OUTPUT_DIR', '.')) if os.getenv('OUTPUT_DIR') else None
        )
