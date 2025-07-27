import fitz
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.analysis_new import DocumentAnalyzer, TextBlock

def debug_file04():
    pdf_path = "input/file04.pdf"
    blocks = []
    
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]  # Only one page
        page_width = page.rect.width
        
        print(f"Page width: {page_width}")
        print("=" * 50)
        
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
                                page_num=0
                            )
                            blocks.append(text_block)
                            
                            # Show uppercase blocks and large font blocks
                            if (text_block.text_case == "UPPER" and len(text_block.text.strip()) > 5) or text_block.font_size >= 12:
                                print(f"Text: '{text_block.text}' | Font: {text_block.font_size:.1f} | "
                                      f"Bold: {text_block.is_bold} | Pos: ({text_block.x_position:.1f}, {text_block.y_position:.1f}) | "
                                      f"Case: {text_block.text_case} | Centered: {text_block.is_centered}")
        
        print("=" * 50)
        print("Running analysis...")
        
        analyzer = DocumentAnalyzer()
        analyzer.set_page_width(page_width)
        
        for block in blocks:
            analyzer.add_text_block(block)
        
        title, outline = analyzer.analyze_document()
        print(f"Title: '{title}'")
        print(f"Outline: {outline}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_file04()
