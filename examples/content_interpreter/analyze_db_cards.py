"""Analyze all cards from the main MCard database."""
import os
import json
import subprocess
from pathlib import Path
from mcard import MCardStorage
from dotenv import load_dotenv

def get_db_path():
    """Get the database path from .env file."""
    load_dotenv()
    db_path = os.getenv('MCARD_DB', 'data/db/MCardStore.db')
    # Convert relative path to absolute path
    if not os.path.isabs(db_path):
        root_dir = Path(__file__).parent.parent.parent
        db_path = os.path.join(root_dir, db_path)
    return db_path

def analyze_card(hash_value):
    """Analyze a single card using the content interpreter."""
    print(f"\n{'='*80}")
    print(f"Analyzing card: {hash_value}")
    print('='*80)
    
    result = subprocess.run(
        ['python3', 'app.py', hash_value],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    try:
        # Parse and pretty print the JSON output
        analysis = json.loads(result.stdout)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        return analysis
    except json.JSONDecodeError:
        print("Raw output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        return None

def main():
    # Get database path
    db_path = get_db_path()
    print(f"Using database: {db_path}")
    
    # Initialize storage
    storage = MCardStorage(db_path)
    
    # Get all cards from the database
    collection = storage.get_all()
    
    if not collection:
        print("No cards found in the database.")
        return
    
    print(f"Found {len(collection)} cards in the database.")
    
    # Analyze each card
    results = []
    for card in collection:
        analysis = analyze_card(card.content_hash)
        if analysis:
            results.append({
                'hash': card.content_hash,
                'analysis': analysis
            })
    
    # Save the complete analysis to a JSON file
    output_file = Path(__file__).parent / 'analysis_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nComplete analysis saved to: {output_file}")
    
    # Print summary statistics
    mime_types = {}
    languages = {}
    
    for result in results:
        analysis = result['analysis']
        mime_type = analysis['mime_type']
        mime_types[mime_type] = mime_types.get(mime_type, 0) + 1
        
        for lang in analysis.get('languages', []):
            lang_code = lang['lang']
            languages[lang_code] = languages.get(lang_code, 0) + 1
    
    print("\nAnalysis Summary:")
    print("\nMIME Types Distribution:")
    for mime_type, count in mime_types.items():
        print(f"  {mime_type}: {count} cards")
    
    if languages:
        print("\nLanguages Distribution:")
        for lang, count in languages.items():
            print(f"  {lang}: {count} cards")

if __name__ == "__main__":
    main()
