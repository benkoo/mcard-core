# MCard Content Analyzer

This example demonstrates how to use the MCard library to analyze content from various sources, showcasing the possibility of performing multiple content transformations within a single processing step. While this implementation combines several analyses into one operation, it serves as a stepping stone towards a more purely functional approach based on Category Theory.

## Theoretical Background

MCard can be understood as a concrete implementation of morphisms from Category Theory. In this context:

1. **Morphisms as Transformations**
   - Each MCard represents a morphism (a structure-preserving map between objects)
   - Content transformations (MIME detection, language detection, summarization) are morphisms
   - Compositions of transformations form new morphisms

2. **Lambda Calculus Connection**
   The transformations in this analyzer correspond to Lambda Calculus's basic abstractions:
   - **Alpha Abstraction**: Content transformation with preserved meaning (e.g., text encoding)
   - **Beta Abstraction**: Applying analysis functions to content
   - **Eta Abstraction**: Different analysis paths yielding equivalent results

3. **Pure Functional Approach**
   Like HyperCard and HyperTalk before it, MCard can serve as a general-purpose programming language by:
   - Representing each transformation as a pure function
   - Enabling composition of transformations
   - Maintaining referential transparency
   - Tracking data lineage through transformation chains

The current implementation, while functional, combines multiple morphisms into a single step. Future versions will decompose these into individual, traceable transformations.

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

To align more closely with Category Theory and Lambda Calculus principles:

1. **Pure Morphisms**
   - Each transformation becomes a pure morphism
   - Functions are stateless and deterministic
   - Transformations preserve categorical properties

2. **MCard as Morphism**
   - Each MCard explicitly represents a morphism
   - Morphism metadata stored with transformation
   - Clear input and output types defined

3. **Functorial Mapping**
   - Create category-preserving mappings between transformations
   - Enable formal verification of transformation properties
   - Support natural transformations between different representations

4. **Composition Chains**
   - Build transformation pipelines as morphism compositions
   - Maintain categorical laws (associativity, identity)
   - Track morphism applications for debugging

This evolution will create a theoretically sound, purely functional content analysis system with guaranteed properties and clear transformation semantics.
