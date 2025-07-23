#!/usr/bin/env python3
"""
Test script for PDF Outline Extractor
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from utils.analysis import DocumentAnalyzer, TextBlock
    print("✅ Successfully imported analysis modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_text_block():
    """Test TextBlock functionality."""
    print("\n=== Testing TextBlock ===")
    
    # Create a test text block
    block = TextBlock(
        text="Chapter 1: Introduction",
        font_size=16.0,
        font_name="Arial-Bold",
        bbox=(72, 100, 200, 120),
        page_num=1
    )
    
    print(f"Text: {block.text}")
    print(f"Font size: {block.font_size}")
    print(f"Is bold: {block.is_bold}")
    print(f"Is all caps: {block.is_all_caps}")
    print(f"Indentation: {block.get_indentation()}")
    

def test_document_analyzer():
    """Test DocumentAnalyzer functionality."""
    print("\n=== Testing DocumentAnalyzer ===")
    
    analyzer = DocumentAnalyzer()
    
    # Create sample text blocks
    blocks = [
        TextBlock("Understanding AI", 18.0, "Arial-Bold", (100, 50, 300, 70), 1),
        TextBlock("This is body text about artificial intelligence...", 12.0, "Arial", (72, 100, 400, 115), 1),
        TextBlock("Chapter 1: Introduction", 14.0, "Arial-Bold", (72, 150, 250, 165), 1),
        TextBlock("More body text here about the introduction...", 12.0, "Arial", (72, 180, 400, 195), 1),
        TextBlock("1.1 What is AI?", 13.0, "Arial-Bold", (90, 220, 200, 235), 1),
        TextBlock("Artificial intelligence is...", 12.0, "Arial", (90, 250, 400, 265), 1),
    ]
    
    # Add blocks to analyzer
    for block in blocks:
        analyzer.add_text_block(block)
    
    # Analyze document
    analyzer.analyze_document()
    
    print(f"Baseline font size: {analyzer.baseline_font_size}")
    print(f"Baseline font name: {analyzer.baseline_font_name}")
    
    # Find title
    title = analyzer.find_title()
    print(f"Title: {title.text if title else 'None found'}")
    
    # Extract headings
    headings = analyzer.extract_headings(min_score=15.0)
    print(f"Found {len(headings)} headings:")
    
    for heading in headings:
        print(f"  - {heading.text} (score: {heading.heading_score:.1f})")
    
    # Assign levels
    outline = analyzer.assign_heading_levels(headings)
    print("\nOutline structure:")
    for item in outline:
        print(f"  {item['level']}: {item['text']} (page {item['page']})")


def test_numbering_detection():
    """Test numbering pattern detection."""
    print("\n=== Testing Numbering Detection ===")
    
    analyzer = DocumentAnalyzer()
    
    test_texts = [
        "1. Introduction",
        "1.1 Overview",
        "1.1.1 Background",
        "Chapter 1",
        "Section A",
        "A. First Point",
        "I. Roman Numeral",
        "Regular text without numbering"
    ]
    
    for text in test_texts:
        has_pattern, level = analyzer.detect_numbering_pattern(text)
        print(f"'{text}' -> Pattern: {has_pattern}, Level: {level}")


def create_sample_json():
    """Create a sample output JSON to show expected format."""
    print("\n=== Creating Sample Output ===")
    
    sample_output = {
        "title": "Understanding Artificial Intelligence",
        "outline": [
            {"level": "H1", "text": "Chapter 1: Introduction", "page": 1},
            {"level": "H2", "text": "1.1 What is AI?", "page": 2},
            {"level": "H3", "text": "1.1.1 History of AI", "page": 3},
            {"level": "H2", "text": "1.2 Types of AI", "page": 4},
            {"level": "H1", "text": "Chapter 2: Applications", "page": 5},
            {"level": "H2", "text": "2.1 Machine Learning", "page": 6},
            {"level": "H2", "text": "2.2 Natural Language Processing", "page": 8}
        ]
    }
    
    # Save sample output
    output_path = os.path.join(current_dir, "sample_output.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_output, f, indent=2, ensure_ascii=False)
    
    print(f"Sample output saved to: {output_path}")
    print("Sample structure:")
    print(json.dumps(sample_output, indent=2))


def main():
    """Run all tests."""
    print("🧪 PDF Outline Extractor - Test Suite")
    print("=" * 50)
    
    try:
        test_text_block()
        test_document_analyzer()
        test_numbering_detection()
        create_sample_json()
        
        print("\n✅ All tests completed successfully!")
        print("\nNext steps:")
        print("1. Build Docker image: docker build -t pdf-extractor .")
        print("2. Add PDF files to ./input/ directory")
        print("3. Run: docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output pdf-extractor")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
