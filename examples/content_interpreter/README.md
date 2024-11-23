# MCard Content Interpreter Example

This example demonstrates how to build a content analysis tool using MCard. The tool analyzes MCard content and produces detailed analysis results including:

1. MIME type detection
2. Language detection (for text content)
3. Content summarization using Ollama's llava model

## Requirements

In addition to MCard's requirements, you'll need:
```
python-magic>=0.4.27
langdetect>=1.0.9
requests>=2.31.0
```

You'll also need:
- Ollama installed and running locally (or specify a different host)
- The llava model pulled in Ollama (`ollama pull llava`)

## Installation

1. Install the required Python packages:
```bash
pip install -r requirements.txt
```

2. Install Ollama from [ollama.ai](https://ollama.ai)

3. Pull the llava model:
```bash
ollama pull llava
```

## Usage

1. Start the Ollama server:
```bash
ollama serve
```

2. Run the interpreter:
```bash
python main.py [--env-file PATH_TO_ENV] [--output-dir OUTPUT_DIR] [--mode {db,test}]
```

Arguments:
- `--env-file`: Path to .env file (optional)
- `--output-dir`: Directory to save results (default: current directory)
- `--mode`: Analysis mode (default: 'db')
  - `db`: Analyze cards from the database
  - `test`: Generate and analyze test cards

## Project Structure

```
.
├── README.md               # This file
├── analysis_results.json   # Analysis results output
├── interpreter/           # Core interpreter package
├── main.py               # Main entry point
├── requirements.txt      # Python dependencies
└── results/             # Directory for analysis results
```

## Features

### MIME Type Detection
Uses `python-magic` to accurately detect the MIME type of any content, including binary data.

### Language Detection
For text content, uses `langdetect` to identify potential languages with probability scores.

### Content Summarization
Uses Ollama's llava model to generate summaries:
- For text: Provides a concise summary of the content
- For images: Generates a description of the image
- Supports multiple languages based on detected content language

## Example Output

Analysis results are saved in JSON format with the following structure:

```json
{
  "mime_type": "text/plain",
  "languages": [
    {
      "lang": "en",
      "prob": 0.999
    }
  ],
  "summary": "A brief summary of the content..."
}
```

For images, the output will look like:
```json
{
  "mime_type": "image/jpeg",
  "languages": [],
  "summary": "The image shows a sunset over a mountain range..."
}
