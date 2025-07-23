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
    print("🔍 Simulating PDF Processing")
    print("=" * 50)
    
    # Simulate text blocks from a typical academic paper or technical document
    simulated_blocks = [
        # Title on first page
        TextBlock("Artificial Intelligence in Modern Applications", 20.0, "Arial-Bold", (150, 80, 450, 105), 1),
        
        # Author info (smaller, should not be detected as heading)
        TextBlock("Dr. Jane Smith, University of Technology", 10.0, "Arial", (200, 110, 400, 125), 1),
        
        # Abstract heading
        TextBlock("Abstract", 14.0, "Arial-Bold", (72, 150, 130, 165), 1),
        TextBlock("This paper presents a comprehensive overview of artificial intelligence applications in various domains. We explore machine learning algorithms, natural language processing techniques, and computer vision systems.", 12.0, "Arial", (72, 170, 520, 210), 1),
        
        # Main content headings
        TextBlock("1. Introduction", 16.0, "Arial-Bold", (72, 250, 200, 270), 1),
        TextBlock("Artificial intelligence has revolutionized many industries over the past decade. This introduction provides background on key concepts and methodologies.", 12.0, "Arial", (72, 280, 520, 320), 1),
        
        TextBlock("1.1 Historical Context", 14.0, "Arial-Bold", (90, 350, 250, 370), 1),
        TextBlock("The field of AI began in the 1950s with the work of pioneers like Alan Turing and John McCarthy.", 12.0, "Arial", (90, 380, 520, 400), 1),
        
        TextBlock("1.2 Current State of the Art", 14.0, "Arial-Bold", (90, 430, 280, 450), 2),
        TextBlock("Modern AI systems leverage deep learning and big data to achieve unprecedented performance.", 12.0, "Arial", (90, 460, 520, 480), 2),
        
        # Chapter 2
        TextBlock("2. Machine Learning Fundamentals", 16.0, "Arial-Bold", (72, 50, 350, 70), 2),
        TextBlock("Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.", 12.0, "Arial", (72, 80, 520, 120), 2),
        
        TextBlock("2.1 Supervised Learning", 14.0, "Arial-Bold", (90, 150, 270, 170), 2),
        TextBlock("Supervised learning algorithms learn from labeled training data to make predictions on new, unseen data.", 12.0, "Arial", (90, 180, 520, 200), 2),
        
        TextBlock("2.1.1 Classification Algorithms", 13.0, "Arial-Bold", (110, 230, 320, 250), 2),
        TextBlock("Classification algorithms predict discrete categories or classes. Examples include decision trees, support vector machines, and neural networks.", 12.0, "Arial", (110, 260, 520, 280), 2),
        
        TextBlock("2.1.2 Regression Algorithms", 13.0, "Arial-Bold", (110, 310, 300, 330), 2),
        TextBlock("Regression algorithms predict continuous numerical values. Linear regression is the simplest example.", 12.0, "Arial", (110, 340, 520, 360), 2),
        
        # Chapter 3
        TextBlock("3. Natural Language Processing", 16.0, "Arial-Bold", (72, 400, 350, 420), 2),
        TextBlock("NLP enables computers to understand, interpret, and generate human language in a valuable way.", 12.0, "Arial", (72, 430, 520, 450), 2),
        
        # Conclusion
        TextBlock("4. Conclusion", 16.0, "Arial-Bold", (72, 50, 200, 70), 3),
        TextBlock("This paper has provided an overview of key AI technologies and their applications.", 12.0, "Arial", (72, 80, 520, 100), 3),
        
        # References (all caps, should be detected)
        TextBlock("REFERENCES", 14.0, "Arial-Bold", (72, 150, 180, 170), 3),
        TextBlock("[1] Smith, J. (2023). Machine Learning Fundamentals. Tech Press.", 10.0, "Arial", (72, 180, 520, 195), 3),
    ]
    
    # Initialize analyzer
    analyzer = DocumentAnalyzer()
    analyzer.page_width = 600  # Typical page width for centering calculations
    
    # Add all blocks
    for block in simulated_blocks:
        analyzer.add_text_block(block)
    
    # Analyze the document
    print(f"Processing {len(simulated_blocks)} text blocks...")
    analyzer.analyze_document()
    
    # Display analysis results
    print(f"\n📊 Analysis Results:")
    print(f"Baseline font size: {analyzer.baseline_font_size}pt")
    print(f"Baseline font name: {analyzer.baseline_font_name}")
    
    # Find title
    title_block = analyzer.find_title()
    title = title_block.text if title_block else "Untitled Document"
    print(f"Detected title: '{title}'")
    
    # Extract headings with different thresholds to show sensitivity
    thresholds = [20.0, 25.0, 30.0]
    
    for threshold in thresholds:
        headings = analyzer.extract_headings(min_score=threshold)
        print(f"\n🎯 Headings detected (threshold: {threshold}):")
        
        for heading in headings[:10]:  # Show first 10
            print(f"  📄 {heading.text[:50]}{'...' if len(heading.text) > 50 else ''}")
            print(f"     Score: {heading.heading_score:.1f}, Font: {heading.font_size}pt, Page: {heading.page_num}")
    
    # Generate final outline with optimal threshold
    headings = analyzer.extract_headings(min_score=25.0)
    outline = analyzer.assign_heading_levels(headings)
    
    # Create final JSON output
    result = {
        "title": title,
        "outline": outline
    }
    
    print(f"\n📝 Final Outline Structure:")
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
    """Show detailed breakdown of the heuristic scoring system."""
    print("\n🧠 Heuristic Scoring Breakdown")
    print("=" * 50)
    
    print("The PDF Outline Extractor uses a multi-factor scoring system:")
    print("\n📏 Font Size Factor:")
    print("  • Score = (font_size / baseline_size - 1) × 50")
    print("  • Example: 16pt vs 12pt baseline = (16/12 - 1) × 50 = 16.7 points")
    
    print("\n💪 Bold Font Factor:")
    print("  • +20 points if font contains: bold, black, heavy, demi, semi")
    
    print("\n🔠 All Caps Factor:")
    print("  • +15 points for ALL CAPS text (under 100 chars)")
    
    print("\n📏 Text Length Factor:")
    print("  • +10 points if text < 100 characters")
    print("  • -10 points if text > 200 characters")
    
    print("\n🔢 Numbering Pattern Factor:")
    print("  • +30 points for numbered patterns (1., 1.1, Chapter 1, etc.)")
    print("  • +5 bonus for 1.1 patterns")
    print("  • +10 bonus for 1.1.1 patterns")
    
    print("\n📍 Position Factors:")
    print("  • +15 points for centered text")
    print("  • +10 points for font name different from baseline")
    print("  • +5 points if on first page")
    
    print("\n🎯 Typical Score Ranges:")
    print("  • Body text: 5-15 points")
    print("  • Minor headings: 25-40 points") 
    print("  • Major headings: 50-80 points")
    print("  • Titles: 70-100+ points")


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
