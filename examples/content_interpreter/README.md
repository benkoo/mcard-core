# MCard Content Interpreter Example

This example demonstrates how to build a content analysis tool using MCard. The tool takes an MCard as input and produces a JSON analysis of its content, including:

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
pip install python-magic langdetect requests
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

2. Run the interpreter with an MCard content hash:
```bash
python app.py <content_hash>
```

The program will output a JSON object with the following structure:
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

For a text document:
```json
{
  "mime_type": "text/plain",
  "languages": [
    {
      "lang": "en",
      "prob": 0.999
    },
    {
      "lang": "fr",
      "prob": 0.001
    }
  ],
  "summary": "This document discusses the implementation of a new feature..."
}
```

For an image:
```json
{
  "mime_type": "image/jpeg",
  "languages": [],
  "summary": "The image shows a sunset over a mountain range..."
}
```

## Error Handling

The interpreter handles various error cases:
- Invalid content hashes
- Network errors with Ollama
- Unsupported content types
- Language detection failures

## Configuration

The Ollama host can be configured by passing it to the ContentInterpreter constructor:
```python
interpreter = ContentInterpreter(ollama_host="http://custom-host:11434")
```
