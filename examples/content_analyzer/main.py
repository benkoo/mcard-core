"""Main script demonstrating the use of the content analyzer."""
import argparse
import json
import os
from pathlib import Path
from mcard import config, load_data, storage
from content_analyzer import ContentAnalyzer, AnalyzerConfig, CardGenerator

def get_ollama_config():
    """Get Ollama configuration from environment."""
    return {
        'host': os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
        'model': os.getenv('OLLAMA_MODEL', 'llava')
    }

def analyze_db_cards(analyzer: ContentAnalyzer, output_dir: Path):
    """Analyze cards from the MCard database."""
    # Initialize storage with default database
    db_path = os.path.join(os.path.dirname(__file__), 'content_analysis.db')
    store = storage.MCardStorage(db_path=db_path)
    
    try:
        # Get all cards from storage
        cards = store.get_all()
        print(f"Loaded {len(cards)} cards from database: {db_path}")
        
        # Analyze cards
        results = analyzer.analyze_cards(cards)
        print(f"Analyzed {len(results)} cards")
        
        # Save detailed results
        analyzer.save_results(results, output_dir / 'analysis_results.json')
        
        # Generate and save summary
        summary = analyzer.generate_summary(results)
        with open(output_dir / 'analysis_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
            
    except Exception as e:
        print(f"Error accessing database: {e}")
        print("Note: If this is the first run, the database will be empty.")
        print("Try running with --mode dir first to analyze files from MCARD_DATA_SOURCE")

def analyze_directory_cards(analyzer: ContentAnalyzer, output_dir: Path):
    """Analyze cards from the data source directory."""
    # Load cards from data source directory
    data_source = config.get_data_source()
    cards = load_data.load_files_from_directory(data_source)
    print(f"Loaded {len(cards)} cards from {data_source}")
    
    # Analyze cards
    results = analyzer.analyze_cards(cards)
    print(f"Analyzed {len(results)} cards")
    
    # Save detailed results
    analyzer.save_results(results, output_dir / 'analysis_results.json')
    
    # Generate and save summary
    summary = analyzer.generate_summary(results)
    with open(output_dir / 'analysis_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

def analyze_test_cards(analyzer: ContentAnalyzer, output_dir: Path):
    """Generate and analyze test cards."""
    # Create test cards
    cards = CardGenerator.create_test_suite()
    print(f"Generated {len(cards)} test cards")
    
    # Analyze cards
    results = analyzer.analyze_cards(cards)
    print(f"Analyzed {len(results)} cards")
    
    # Save detailed results
    analyzer.save_results(results, output_dir / 'analysis_results.json')
    
    # Generate and save summary
    summary = analyzer.generate_summary(results)
    with open(output_dir / 'test_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='MCard Content Analyzer')
    parser.add_argument('--env-file', help='Path to .env file')
    parser.add_argument('--output-dir', type=Path, default=Path('results'),
                      help='Directory to save results')
    parser.add_argument('--mode', choices=['db', 'dir', 'test'], default='db',
                      help='Analysis mode: db (analyze database), dir (analyze data directory), or test (analyze test cards)')
    parser.add_argument('--save-to-db', action='store_true',
                      help='Save analyzed cards to the database (only applicable with dir mode)')
    
    args = parser.parse_args()
    
    # Load environment configuration
    config.load_config(args.env_file)
    
    # Create configuration from environment
    analyzer_config = AnalyzerConfig.from_env(args.env_file)
    
    # Create analyzer
    analyzer = ContentAnalyzer(analyzer_config)
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run analysis based on mode
    if args.mode == 'db':
        analyze_db_cards(analyzer, args.output_dir)
    elif args.mode == 'dir':
        analyze_directory_cards(analyzer, args.output_dir)
        
        # Save to database if requested
        if args.save_to_db:
            try:
                db_path = os.path.join(os.path.dirname(__file__), 'content_analysis.db')
                store = storage.MCardStorage(db_path=db_path)
                
                # Load and store cards
                data_source = config.get_data_source()
                cards = load_data.load_files_from_directory(data_source)
                saved_count = 0
                for card in cards:
                    if store.save(card):
                        saved_count += 1
                print(f"Saved {saved_count} new cards to database: {db_path}")
            except Exception as e:
                print(f"Error saving to database: {e}")
    else:
        analyze_test_cards(analyzer, args.output_dir)

if __name__ == '__main__':
    main()
