import fitz
from utils.analysis_new import DocumentAnalyzer, TextBlock

def debug_file_analysis(filename):
    print(f"\n=== DEBUGGING {filename} ===")
    
    # Load document
    doc = fitz.open(f'input/{filename}')
    text_blocks = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        page_blocks = []
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            bbox = span["bbox"]
                            text_block = TextBlock(
                                text=text,
                                font_size=span["size"],
                                font_name=span["font"],
                                bbox=bbox,
                                page_num=page_num,
                                is_italic=bool(span["flags"] & 2**1)
                            )
                            page_blocks.append(text_block)
        
        # Sort by y-position and calculate space_above
        page_blocks.sort(key=lambda b: (b.y_position, b.x_position))
        
        for i, block in enumerate(page_blocks):
            if i == 0:
                block.space_above = 0
            else:
                prev_block = page_blocks[i-1]
                block.space_above = block.y_position - (prev_block.y_position + prev_block.font_size)
        
        text_blocks.extend(page_blocks)
    
    doc.close()
    
    # Analyze with DocumentAnalyzer
    analyzer = DocumentAnalyzer()
    for block in text_blocks:
        analyzer.add_text_block(block)
    
    title, outline = analyzer.analyze_document()
    
    print(f"Final Result - Title: '{title}', Outline entries: {len(outline)}")
    
    # Debug specific checks
    all_text = " ".join([b.text for b in text_blocks])
    
    if filename == 'file05.pdf':
        print(f"Contains HOPE/SEE/THERE: {any(word in all_text.upper() for word in ['HOPE', 'SEE', 'YOU', 'THERE'])}")
        long_blocks = [b for b in text_blocks if len(b.text) > 50]
        print(f"Long blocks (>50 chars): {len(long_blocks)}")
        for i, block in enumerate(long_blocks):
            print(f"  Long block {i}: '{block.text}' (len={len(block.text)})")
        
        # Check the exact flyer detection condition
        is_simple_flyer = (any(word in all_text.upper() for word in ['HOPE', 'SEE', 'YOU', 'THERE']) and
                          len([b for b in text_blocks if len(b.text) > 50]) < 3)
        print(f"Is simple flyer: {is_simple_flyer}")
        decorative_blocks = []
        for block in text_blocks:
            if (block.font_size > 20 and block.is_bold and 
                any(word in block.text.upper() for word in ['HOPE', 'TO', 'SEE', 'YOU', 'THERE', 'Y', 'T', 'HERE', 'OU', '!'])):
                decorative_blocks.append((block.text, block.font_size, block.y_position, block.x_position))
        
        print(f"All decorative blocks (sorted by X position):")
        decorative_blocks.sort(key=lambda x: x[3])  # Sort by x position
        for text, size, y, x in decorative_blocks:
            print(f"  '{text}' (size={size:.1f}, y={y:.1f}, x={x:.1f})")
        
        # Try to reconstruct
        if decorative_blocks:
            reconstructed = "".join([text for text, _, _, _ in decorative_blocks])
            print(f"Reconstructed text: '{reconstructed}'")
    
    elif filename == 'file02.pdf':
        print(f"Contains overview/foundation: {('overview' in all_text.lower() and 'foundation' in all_text.lower())}")
        
        # Check first page blocks
        first_page_blocks = [b for b in text_blocks if b.page_num == 0 and len(b.text.strip()) > 2]
        print("First page large bold blocks:")
        for block in first_page_blocks[:8]:
            if block.font_size >= 20 and block.is_bold:
                print(f"  '{block.text}' (size={block.font_size}, bold={block.is_bold})")

# Test both files
debug_file_analysis('file05.pdf')
debug_file_analysis('file02.pdf')
