"""Script to update SQLiteConfig references to use engine_config."""
import os
import fileinput
import sys
from pathlib import Path

def update_file(file_path: str):
    """Update SQLiteConfig references in a file."""
    with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
        for line in file:
            # Update import statements
            line = line.replace(
                'from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType',
                'from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType'
            )
            print(line, end='')

def main():
    """Main function to update all files."""
    root_dir = Path(__file__).parent.parent
    python_files = list(root_dir.rglob('*.py'))
    
    for file_path in python_files:
        with open(file_path) as f:
            content = f.read()
            if 'SQLiteConfig' in content:
                print(f'Updating {file_path}...')
                update_file(str(file_path))

if __name__ == '__main__':
    main()
