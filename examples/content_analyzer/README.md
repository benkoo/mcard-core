# MCard Content Analyzer

This example demonstrates how to use the MCard library to analyze content from various sources, showcasing the possibility of performing multiple content transformations within a single processing step. While this implementation combines several analyses into one operation, it serves as a stepping stone towards a more purely functional approach.

## Conceptual Background & Future Direction

This example currently performs multiple content transformations (MIME detection, language detection, summarization) in a single step. However, a more ideal approach, aligned with the principles of Lambda Calculus and Purely Functional Software Configuration (as explored in Eelco Dolstra's doctoral thesis), would be to:

1. Decompose each transformation into an individual MCard function
2. Map each transformation function to a single MCard
3. Create a traceable chain of transformations

This would enable:
- Pure functions where each transformation is isolated and deterministic
- Complete traceability of how each function processes the content
- Composition of transformations in a functional programming style
- Better testing and debugging capabilities
- Easier parallelization and optimization

The current implementation demonstrates the feasibility of content analysis, while future versions could evolve towards this more purely functional approach.

## Current Features

- MIME type detection
- Language detection
- AI-powered content summarization
- AI-powered title generation
- Support for both text and binary content
- Parallel processing of multiple cards
- Results storage in JSON format

## Configuration

The analyzer can be configured using environment variables:

- `MCARD_DATA_SOURCE`: Directory containing data files to analyze
- `MCARD_DB`: Path to MCard database
- `OLLAMA_HOST`: Ollama server host (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model to use (default: llava)

## Usage

```bash
# Analyze cards from database
python main.py --mode db

# Analyze cards from data directory
python main.py --mode dir

# Analyze test cards
python main.py --mode test

# Save analyzed cards to database
python main.py --mode dir --save-to-db
```

## Output

Results are saved in the `results` directory:
- `analysis_results.json`: Detailed analysis of each card
- `analysis_summary.json`: Summary statistics of analyzed cards
- `test_summary.json`: Summary of test card analysis

## Future Improvements

To move towards a more purely functional approach:

1. **Function Decomposition**
   - Split the analyzer into individual, pure functions
   - Each function should handle one specific transformation
   - Functions should be stateless and deterministic

2. **MCard Mapping**
   - Each function should map to a single MCard
   - MCards should contain both the function and its metadata
   - Enable tracking of function inputs, outputs, and dependencies

3. **Transformation Chain**
   - Create a clear pipeline of transformations
   - Enable composition of transformations
   - Maintain history of all transformations

4. **Traceability**
   - Log each transformation step
   - Track data lineage
   - Enable debugging and optimization

This evolution would align the implementation more closely with functional programming principles and enable better composition, testing, and maintenance of the content analysis system.
