#!/usr/bin/env python3
"""
Demonstration script showing how the PDF Outline Extractor works
without requiring actual PDF files.
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from utils.analysis import DocumentAnalyzer, TextBlock


def simulate_pdf_processing():
    """Simulate processing a real PDF document."""
    print("🔍 Simulating PDF Processing with Two-Pass Algorithm")
    print("=" * 60)
    
    # Simulate text blocks from a typical academic paper or technical document
    # Note: is_italic is now a required argument for TextBlock
    simulated_blocks = [
        # Title on first page
        TextBlock("Artificial Intelligence in Modern Applications", 20.0, "Arial-Bold", (150, 80, 450, 105), 0, False),
        
        # Author info (smaller, should not be detected as heading)
        TextBlock("Dr. Jane Smith, University of Technology", 10.0, "Arial", (200, 110, 400, 125), 0, False),
        
        # Abstract heading
        TextBlock("Abstract", 14.0, "Arial-Bold", (72, 150, 130, 165), 0, False),
        TextBlock("This paper presents a comprehensive overview of artificial intelligence applications in various domains. We explore machine learning algorithms, natural language processing techniques, and computer vision systems.", 12.0, "Arial", (72, 170, 520, 210), 0, False),
        
        # Main content headings
        TextBlock("1. Introduction", 16.0, "Arial-Bold", (72, 250, 200, 270), 0, False),
        TextBlock("Artificial intelligence has revolutionized many industries over the past decade. This introduction provides background on key concepts and methodologies.", 12.0, "Arial", (72, 280, 520, 320), 0, False),
        
        TextBlock("1.1 Historical Context", 14.0, "Arial-Bold", (90, 350, 250, 370), 0, True), # Italic
        TextBlock("The field of AI began in the 1950s with the work of pioneers like Alan Turing and John McCarthy.", 12.0, "Arial", (90, 380, 520, 400), 0, False),
        
        TextBlock("1.2 Current State of the Art", 14.0, "Arial-Bold", (90, 430, 280, 450), 1, True), # Italic
        TextBlock("Modern AI systems leverage deep learning and big data to achieve unprecedented performance.", 12.0, "Arial", (90, 460, 520, 480), 1, False),
        
        # Chapter 2
        TextBlock("2. Machine Learning Fundamentals", 16.0, "Arial-Bold", (72, 50, 350, 70), 1, False),
        TextBlock("Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.", 12.0, "Arial", (72, 80, 520, 120), 1, False),
        
        TextBlock("2.1 Supervised Learning", 14.0, "Arial-Bold", (90, 150, 270, 170), 1, False),
        TextBlock("Supervised learning algorithms learn from labeled training data to make predictions on new, unseen data.", 12.0, "Arial", (90, 180, 520, 200), 1, False),
        
        TextBlock("2.1.1 Classification Algorithms", 13.0, "Arial-Bold", (110, 230, 320, 250), 1, False),
        TextBlock("Classification algorithms predict discrete categories or classes. Examples include decision trees, support vector machines, and neural networks.", 12.0, "Arial", (110, 260, 520, 280), 1, False),
        
        TextBlock("2.1.2 Regression Algorithms", 13.0, "Arial-Bold", (110, 310, 300, 330), 1, False),
        TextBlock("Regression algorithms predict continuous numerical values. Linear regression is the simplest example.", 12.0, "Arial", (110, 340, 520, 360), 1, False),
        
        # Chapter 3
        TextBlock("3. Natural Language Processing", 16.0, "Arial-Bold", (72, 400, 350, 420), 1, False),
        TextBlock("NLP enables computers to understand, interpret, and generate human language in a valuable way.", 12.0, "Arial", (72, 430, 520, 450), 1, False),
        
        # Conclusion
        TextBlock("4. Conclusion", 16.0, "Arial-Bold", (72, 50, 200, 70), 2, False),
        TextBlock("This paper has provided an overview of key AI technologies and their applications.", 12.0, "Arial", (72, 80, 520, 100), 2, False),
        
        # References (all caps, should be detected)
        TextBlock("REFERENCES", 14.0, "Arial-Bold", (72, 150, 180, 170), 2, False),
        TextBlock("[1] Smith, J. (2023). Machine Learning Fundamentals. Tech Press.", 10.0, "Arial", (72, 180, 520, 195), 2, False),
    ]
    
    # Initialize analyzer
    analyzer = DocumentAnalyzer()
    
    # Add all blocks
    for block in simulated_blocks:
        analyzer.add_text_block(block)
    
    # Run the full two-pass analysis
    print(f"Processing {len(simulated_blocks)} text blocks...")
    title, outline = analyzer.analyze_document()
    
    # Display analysis results from the first pass
    print("\n📊 Global Analysis (First Pass) Results:")
    print(f"  • Body Text Style: {analyzer.body_font_size:.2f}pt '{analyzer.body_font_name}'")
    print(f"  • Unique Font Sizes: {analyzer.unique_font_sizes}")
    
    # Create final JSON output
    result = {
        "title": title,
        "outline": outline
    }
    
    print(f"\n📝 Final Outline Structure (from Second Pass & Hierarchy Assignment):")
    print(f"Title: {result['title']}")
    print(f"Headings found: {len(result['outline'])}")
    
    for item in result['outline']:
        indent = "  " * (1 if item['level'] == 'H1' else 2 if item['level'] == 'H2' else 3)
        print(f"{indent}{item['level']}: {item['text']} (page {item['page']})")
    
    # Save demo output
    output_path = os.path.join(current_dir, "demo_output.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Demo output saved to: {output_path}")
    
    return result


def show_heuristic_details():
    """Show detailed breakdown of the new two-pass algorithm."""
    print("\n🧠 Two-Pass Algorithm Breakdown")
    print("=" * 60)
    
    print("The extractor uses a two-pass algorithm for higher accuracy:")
    
    print("\n1️⃣ Pass 1: Global Analysis")
    print("  • The entire document is scanned to find the most common font size and name.")
    print("  • This establishes a baseline for what 'body text' looks like.")
    print("  • All unique font sizes are also collected.")
    
    print("\n2️⃣ Pass 2: Classification & Scoring")
    print("  • Each line is scored based on several rules:")
    print("    - FONT SIZE: Larger than body text? (+ score)")
    print("    - BOLDNESS: Is the text bold? (strong + score)")
    print("    - ALL CAPS: Is the text in ALL CAPS? (+ score)")
    print("    - NUMBERING: Does it start with '1.1', 'Chapter 2', etc.? (strong + score)")
    print("    - SPACING: Is there extra vertical space above the line? (+ score)")
    
    print("\n👑 Title & Hierarchy Assignment")
    print("  • The highest-scoring item on the first page is usually the TITLE.")
    print("  • Headings are clustered by font size and boldness.")
    print("  • Clusters are ranked to assign H1, H2, H3 levels.")
    print("  • The final outline is sorted by page and position.")


if __name__ == "__main__":
    print("🤖 PDF Outline Extractor - Live Demonstration")
    print("=" * 60)
    
    try:
        result = simulate_pdf_processing()
        show_heuristic_details()
        
        print("\n✅ Demonstration completed successfully!")
        print("\n🚀 Ready for real PDF processing!")
        print("Next steps:")
        print("1. docker build -t pdf-extractor .")
        print("2. Place PDFs in ./input/ directory") 
        print("3. docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output pdf-extractor")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
