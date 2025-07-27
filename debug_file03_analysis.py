import fitz
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.analysis_new import DocumentAnalyzer, TextBlock

def debug_file03_structure():
    pdf_path = "input/file03.pdf"
    blocks = []
    
    try:
        doc = fitz.open(pdf_path)
        
        print("=== FILE03 ANALYSIS ===")
        print(f"Total pages: {len(doc)}")
        
        # Analyze first few pages where the expected content should be
        for page_num in range(min(5, len(doc))):
            page = doc[page_num]
            print(f"\n--- PAGE {page_num} ---")
            
            page_blocks = []
            for b in page.get_text("dict")["blocks"]:
                if "lines" in b:
                    for line in b["lines"]:
                        merged_spans = []
                        current_text = ""
                        current_bbox = None
                        current_font = None
                        current_size = None
                        
                        for span in line["spans"]:
                            if not span["text"].strip():
                                continue
                            
                            if (current_font is None or 
                                span["font"] != current_font or 
                                abs(span["size"] - current_size) > 0.5):
                                
                                if current_text.strip():
                                    merged_spans.append({
                                        "text": current_text,
                                        "bbox": current_bbox,
                                        "font": current_font,
                                        "size": current_size
                                    })
                                
                                current_text = span["text"]
                                current_bbox = span["bbox"]
                                current_font = span["font"]
                                current_size = span["size"]
                            else:
                                gap = span["bbox"][0] - current_bbox[2]
                                if gap > current_size * 0.1:
                                    current_text += " " + span["text"]
                                else:
                                    current_text += span["text"]
                                current_bbox = (
                                    current_bbox[0],
                                    current_bbox[1],
                                    span["bbox"][2],
                                    max(current_bbox[3], span["bbox"][3])
                                )
                        
                        if current_text.strip():
                            merged_spans.append({
                                "text": current_text,
                                "bbox": current_bbox,
                                "font": current_font,
                                "size": current_size
                            })
                        
                        for span in merged_spans:
                            if span["text"].strip():
                                text_block = TextBlock(
                                    text=span["text"],
                                    font_size=span["size"],
                                    font_name=span["font"],
                                    bbox=span["bbox"],
                                    page_num=page_num
                                )
                                page_blocks.append(text_block)
                                blocks.append(text_block)
            
            # Show largest fonts and potential headings on this page
            page_blocks.sort(key=lambda x: -x.font_size)
            for i, block in enumerate(page_blocks[:8]):  # Top 8 largest fonts
                print(f"  {i+1}. '{block.text[:60]}...' | Font: {block.font_size:.1f} | Bold: {block.is_bold} | Y: {block.y_position:.1f}")
        
        print("\n=== CHECKING TITLE AREA (PAGE 0) ===")
        # Focus on title area specifically
        first_page_blocks = [b for b in blocks if b.page_num == 0]
        first_page_blocks.sort(key=lambda x: (-x.font_size, x.y_position))
        
        print("Title candidates (largest fonts first):")
        for i, block in enumerate(first_page_blocks[:10]):
            print(f"  {i+1}. '{block.text}' | Font: {block.font_size:.1f} | Bold: {block.is_bold} | Centered: {block.is_centered}")
        
        print("\n=== ANALYSIS RESULTS ===")
        analyzer = DocumentAnalyzer()
        analyzer.set_page_width(doc[0].rect.width)
        
        for block in blocks:
            analyzer.add_text_block(block)
        
        title, outline = analyzer.analyze_document()
        print(f"Detected Title: '{title}'")
        print(f"Outline items: {len(outline)}")
        for i, item in enumerate(outline[:10]):  # First 10 items
            print(f"  {i+1}. {item}")
        
        doc.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_file03_structure()
