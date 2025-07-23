#!/bin/bash
# Build and run script for PDF Outline Extractor

echo "🐳 PDF Outline Extractor - Build & Run"
echo "======================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t pdf-extractor .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

# Create input and output directories if they don't exist
mkdir -p input output

# Check if there are any PDF files in input directory
pdf_count=$(find input -name "*.pdf" 2>/dev/null | wc -l)

if [ $pdf_count -eq 0 ]; then
    echo "⚠️  No PDF files found in ./input/ directory"
    echo "   Please add some PDF files to process"
    echo ""
    echo "📁 Current directory structure:"
    ls -la
    echo ""
    echo "To run the extractor once you have PDFs:"
    echo "docker run -v \$(pwd)/input:/app/input -v \$(pwd)/output:/app/output pdf-extractor"
else
    echo "📄 Found $pdf_count PDF file(s) in ./input/"
    echo "🚀 Running PDF extraction..."
    
    # Run the container
    docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" pdf-extractor
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ PDF extraction completed!"
        echo "📁 Output files:"
        ls -la output/
    else
        echo "❌ PDF extraction failed"
        exit 1
    fi
fi

echo ""
echo "🎉 Ready to process PDFs!"
