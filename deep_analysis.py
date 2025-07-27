import fitz
import sys
import os
import re

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.analysis_new import DocumentAnalyzer, TextBlock

def deep_analysis_file02():
    pdf_path = "input/file02.pdf"
    
    print("=== DEEP ANALYSIS FILE02 ===")
    
    try:
        doc = fitz.open(pdf_path)
        
        # Analyze title area more carefully
        page0 = doc[0]
        print("\n--- TITLE AREA ANALYSIS ---")
        
        title_blocks = []
        for b in page0.get_text("dict")["blocks"]:
            if "lines" in b:
                for line in b["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip() and span["size"] >= 20:
                            print(f"Large text: '{span['text']}' | Size: {span['size']:.1f} | Y: {span['bbox'][1]:.1f} | Font: {span['font']}")
        
        # Check the exact content that should be H1 headings
        print("\n--- H1 CANDIDATES ANALYSIS ---")
        expected_h1_texts = [
            "Revision History",
            "Table of Contents", 
            "Acknowledgements",
            "Introduction to the Foundation Level Extensions",
            "Introduction to Foundation Level Agile Tester Extension"
        ]
        
        for page_num in range(min(7, len(doc))):
            page = doc[page_num]
            print(f"\n-- Page {page_num} --")
            
            for b in page.get_text("dict")["blocks"]:
                if "lines" in b:
                    for line in b["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"]
                        
                        line_text = line_text.strip()
                        
                        # Check if this line matches any expected H1
                        for expected in expected_h1_texts:
                            if expected.lower() in line_text.lower() and len(line_text) < len(expected) + 10:
                                spans_info = [(s["text"], s["size"], s["font"]) for s in line["spans"] if s["text"].strip()]
                                print(f"FOUND H1 CANDIDATE: '{line_text}' | Spans: {spans_info}")
        
        doc.close()
        
    except Exception as e:
        print(f"Error: {e}")

def deep_analysis_file03():
    pdf_path = "input/file03.pdf"
    
    print("\n\n=== DEEP ANALYSIS FILE03 ===")
    
    try:
        doc = fitz.open(pdf_path)
        
        # Analyze the title fragmentation issue more carefully
        page0 = doc[0]
        print("\n--- TITLE FRAGMENTATION ANALYSIS ---")
        
        # Get all spans from the title area and see their exact positions
        title_spans = []
        for b in page0.get_text("dict")["blocks"]:
            if "lines" in b:
                for line in b["lines"]:
                    for span in line["spans"]:
                        if span["size"] >= 30:  # Large title font
                            title_spans.append({
                                'text': span['text'],
                                'x': span['bbox'][0],
                                'y': span['bbox'][1],
                                'size': span['size'],
                                'font': span['font']
                            })
        
        # Sort by position to see the reading order
        title_spans.sort(key=lambda x: (x['y'], x['x']))
        
        print("Title spans in reading order:")
        for i, span in enumerate(title_spans):
            print(f"{i+1}. '{span['text']}' at ({span['x']:.1f}, {span['y']:.1f}) size {span['size']:.1f}")
        
        # Check expected page 1 content
        print("\n--- PAGE 1 CONTENT ANALYSIS ---")
        if len(doc) > 1:
            page1 = doc[1]
            expected_page1_content = [
                "Ontario's Digital Library",
                "A Critical Component for Implementing Ontario's Road Map to Prosperity Strategy",
                "Summary",
                "Timeline:"
            ]
            
            for b in page1.get_text("dict")["blocks"]:
                if "lines" in b:
                    for line in b["lines"]:
                        line_text = ""
                        max_size = 0
                        for span in line["spans"]:
                            line_text += span["text"]
                            max_size = max(max_size, span["size"])
                        
                        line_text = line_text.strip()
                        
                        for expected in expected_page1_content:
                            if expected.lower() in line_text.lower() and len(line_text) <= len(expected) + 5:
                                print(f"FOUND PAGE 1 HEADING: '{line_text}' | Size: {max_size:.1f}")
        
        doc.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deep_analysis_file02()
    deep_analysis_file03()
