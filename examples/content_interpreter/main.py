"""Main script demonstrating the use of the content interpreter package."""
import argparse
import json
from pathlib import Path
from interpreter import (
    InterpreterConfig,
    BatchAnalyzer,
    CardGenerator
)

def analyze_db(config: InterpreterConfig):
    """Analyze cards from the database."""
    analyzer = BatchAnalyzer(config)
    results = analyzer.analyze_from_db()
    analyzer.save_results(results)
    
    # Generate and save summary
    summary = analyzer.generate_summary(results)
    with open(config.output_dir / 'analysis_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

def analyze_test_cards(config: InterpreterConfig):
    """Generate and analyze test cards."""
    generator = CardGenerator()
    cards = generator.create_test_suite()
    
    analyzer = BatchAnalyzer(config)
    results = analyzer.analyze_cards(cards)
    analyzer.save_results(results)
    
    # Generate and save summary
    summary = analyzer.generate_summary(results)
    with open(config.output_dir / 'test_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='MCard Content Interpreter')
    parser.add_argument('--env-file', help='Path to .env file')
    parser.add_argument('--output-dir', type=Path, default=Path('.'),
                      help='Directory to save results')
    parser.add_argument('--mode', choices=['db', 'test'], default='db',
                      help='Analysis mode: db (analyze database) or test (analyze test cards)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = InterpreterConfig.from_env(args.env_file)
    config.output_dir = args.output_dir
    
    # Create output directory if it doesn't exist
    config.output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.mode == 'db':
        analyze_db(config)
    else:
        analyze_test_cards(config)

if __name__ == '__main__':
    main()
