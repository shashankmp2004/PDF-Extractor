import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.analysis_new import DocumentAnalyzer, TextBlock
import fitz

def extract_text_blocks_from_pdf(pdf_path: str):
    blocks = []
    page_width = 0.0
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            if i == 0:
                page_width = page.rect.width
            for b in page.get_text("dict")["blocks"]:
                if "lines" in b:
                    for line in b["lines"]:
                        for span in line["spans"]:
                            if span["text"].strip():
                                block = TextBlock(
                                    text=span["text"], 
                                    font_size=span["size"], 
                                    font_name=span["font"],
                                    bbox=span["bbox"],
                                    page_num=i,
                                    is_italic=bool(span["flags"] & 2**1)
                                )
                                blocks.append(block)
    except Exception as e:
        print(f"Error: {e}")
    return blocks, page_width

# Process file02
pdf_path = "input/file02.pdf"
text_blocks, page_width = extract_text_blocks_from_pdf(pdf_path)

analyzer = DocumentAnalyzer()
analyzer.set_page_width(page_width)
for b in text_blocks:
    analyzer.add_text_block(b)

title, outline = analyzer.analyze_document()

print('Font size tiers:', getattr(analyzer, 'heading_size_tiers', 'Not set'))
print('Baseline font size:', analyzer.baseline_font_size)
print('\nTitle-related blocks:')
for block in analyzer.text_blocks:
    if any(word in block.text.lower() for word in ['overview', 'foundation', 'revision', 'table', 'acknowledgements']):
        print(f'  "{block.text.strip()}" -> {block.font_size}pt, bold={block.is_bold}, page={block.page_num}')

print('\nHeading candidates by font size:')
font_sizes = {}
for block in analyzer.text_blocks:
    if block.font_size not in font_sizes:
        font_sizes[block.font_size] = []
    font_sizes[block.font_size].append(block)

for size in sorted(font_sizes.keys(), reverse=True):
    blocks = font_sizes[size]
    print(f'\n{size}pt ({len(blocks)} blocks):')
    for block in blocks[:5]:  # Show first 5 examples
        print(f'  "{block.text.strip()[:50]}" bold={block.is_bold}')
