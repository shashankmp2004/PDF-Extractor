# PDF Outline Extractor

A Docker-based solution for extracting document outlines from PDF files. This tool processes PDF files and generates structured JSON output containing the document title and heading hierarchy.

## Features

- Automatic PDF processing from input directory
- Generates structured JSON output with title and outline
- Document type detection (forms, posters, technical documents)
- Advanced text reconstruction and heading classification
- Font size-based heading level detection
- Network-isolated execution for security

## Requirements

- Docker with linux/amd64 platform support
- CPU-only execution (no GPU required)
- 8 CPUs and 16 GB RAM recommended
- No internet access required during execution

## Usage

### Building the Docker Image

```bash
docker build --platform linux/amd64 -t pdf-extractor:latest .
```

### Running the Container

```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-extractor:latest
```

### Directory Structure

```
├── input/          # Place PDF files here
├── output/         # JSON output files generated here
├── Dockerfile      # Docker build configuration
├── extract_outline.py  # Main extraction script
├── utils/          # Analysis utilities
│   └── analysis_new.py
└── requirements.txt    # Python dependencies
```

### Output Format

For each `filename.pdf` in the input directory, the tool generates `filename.json` with the following structure:

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Chapter Title ",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "Section Title ",
      "page": 2
    }
  ]
}
```

## Performance

- Processing time: ≤ 10 seconds for a 50-page PDF
- Memory efficient: No model files > 200MB
- CPU-optimized for amd64 architecture

## Dependencies

- Python 3.9
- PyMuPDF (fitz) for PDF processing
- Standard library modules only

## Technical Approach

### Document Analysis Pipeline

1. **Text Extraction**: Uses PyMuPDF to extract text blocks with font information
2. **Document Classification**: Detects document type (poster, form, technical document)
3. **Font Analysis**: Calculates baseline font size and heading size tiers
4. **Text Reconstruction**: Merges fragmented text and handles overlapping spans
5. **Heading Detection**: Uses font size, position, and content patterns
6. **Title Extraction**: Identifies main document title using multiple strategies
7. **Outline Generation**: Creates hierarchical structure with proper heading levels

### Key Features

- **Span Merging**: Combines fragmented text spans with gap detection
- **Font Size Tiers**: Calculates distinct heading levels from font distribution
- **Overlapping Text Handling**: Resolves duplicate content from overlapping spans
- **Generic Document Processing**: No hardcoded rules for specific document types
