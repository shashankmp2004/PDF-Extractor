# PDF Outline Extractor

A high-performance document analysis tool that extracts hierarchical structure (Title, H1, H2, H3) from PDF files and outputs clean, structured JSON files.

## 🚀 Features

- **Smart Heuristic Engine**: Analyzes multiple text properties (font size, weight, positioning, numbering patterns)
- **Multi-core Processing**: Parallel processing for batch operations
- **Docker Ready**: Containerized for consistent deployment
- **High Performance**: Processes 50-page PDFs in under 10 seconds
- **Robust Analysis**: Doesn't rely solely on font size for heading detection

## 🛠️ Technology Stack

- **Language**: Python 3.9
- **PDF Processing**: PyMuPDF (Fitz)
- **Containerization**: Docker
- **Parallel Processing**: Python multiprocessing

## 📁 Project Structure

```
pdf-outline-extractor/
├── Dockerfile
├── requirements.txt
├── extract_outline.py      # Main extraction script
├── test_extractor.py       # Test suite
├── utils/
│   ├── __init__.py
│   └── analysis.py         # Heuristic analysis engine
├── input/                  # Place PDF files here
├── output/                 # JSON outputs generated here
└── README.md
```

## 🏃‍♂️ Quick Start

### 1. Build Docker Image

```bash
docker build -t pdf-extractor .
```

### 2. Prepare Input Files

Place your PDF files in the `input/` directory:

```bash
# Example: copy your PDFs
cp /path/to/your/documents/*.pdf ./input/
```

### 3. Run Extraction

```bash
# Run with mounted volumes
docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output pdf-extractor
```

For Windows PowerShell:
```powershell
docker run -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output pdf-extractor
```

### 4. Check Results

JSON files will be generated in the `output/` directory with the same name as your PDFs.

## 📋 Output Format

Each PDF generates a JSON file with this structure:

```json
{
  "title": "Understanding Artificial Intelligence",
  "outline": [
    {"level": "H1", "text": "Chapter 1: Introduction", "page": 1},
    {"level": "H2", "text": "1.1 What is AI?", "page": 2},
    {"level": "H3", "text": "1.1.1 History of AI", "page": 3},
    {"level": "H2", "text": "1.2 Types of AI", "page": 4}
  ]
}
```

## 🧪 Testing

Run the test suite to verify functionality:

```bash
# Local testing (without Docker)
python test_extractor.py

# Development mode (uses local input/output dirs)
python extract_outline.py --dev
```

## 🔍 How It Works

### 1. Text Extraction
- Extracts all text blocks with formatting metadata (font size, name, position)
- Preserves spatial relationships and page information

### 2. Baseline Analysis
- Identifies the most common font size and style (body text baseline)
- Uses statistical analysis to establish document norms

### 3. Heuristic Scoring
The engine scores each text block based on:
- **Font Size**: Deviation from baseline
- **Font Weight**: Bold vs regular text
- **Text Case**: ALL CAPS detection
- **Numbering Patterns**: Regex matching for "1.", "1.1", "Chapter 1", etc.
- **Positioning**: Centered text, indentation levels
- **Length**: Heading-appropriate text length

### 4. Hierarchy Assignment
- Clusters headings by similar properties
- Assigns H1/H2/H3 levels based on prominence
- Uses numbering patterns to override and refine levels

## ⚡ Performance Optimizations

- **Parallel Processing**: Utilizes multiprocessing for batch operations
- **Efficient Libraries**: PyMuPDF for fast PDF parsing
- **Smart Filtering**: Reduces processing overhead with targeted analysis
- **Memory Management**: Processes files individually to avoid memory issues

## 🔧 Configuration

### Minimum Heading Score
Adjust the minimum score threshold in `extract_outline.py`:

```python
headings = analyzer.extract_headings(min_score=25.0)  # Default: 25.0
```

### Parallel Processing
The system automatically uses available CPU cores (max 8). To force sequential processing:

```python
num_processes = 1  # Force single-threaded processing
```

## 🐛 Troubleshooting

### Common Issues

1. **No headings detected**: Lower the `min_score` threshold
2. **Too many false positives**: Increase the `min_score` threshold
3. **Memory issues**: Ensure sufficient RAM for large PDFs
4. **Permission errors**: Check Docker volume mount permissions

### Debug Mode

Enable verbose output by modifying the main script:

```python
# Add debug prints in process_single_pdf method
print(f"Analyzing {len(text_blocks)} text blocks")
print(f"Baseline: {analyzer.baseline_font_size}pt {analyzer.baseline_font_name}")
```

## 📊 Performance Targets

- **Speed**: ≤ 10 seconds for 50-page PDF
- **Accuracy**: High precision heading detection
- **Scalability**: Batch processing of multiple files
- **Resource Usage**: Optimized for 8 CPU, 16GB RAM environment

## 🌐 Multilingual Support

The system includes basic support for:
- English numbering patterns
- Japanese document structures (planned enhancement)
- Unicode text handling

## 📈 Future Enhancements

- Machine learning model integration
- Custom regex pattern configuration
- Interactive web interface
- Advanced positioning analysis
- Table of contents validation

## 📜 License

This project is part of the Adobe PDF Challenge implementation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

**Note**: This implementation prioritizes accuracy and performance while maintaining simplicity and maintainability.
