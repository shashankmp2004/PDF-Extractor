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
            for b in page.get_text('dict')['blocks']:
                if 'lines' in b:
                    for line in b['lines']:
                        for span in line['spans']:
                            if span['text'].strip():
                                block = TextBlock(
                                    text=span['text'], 
                                    font_size=span['size'], 
                                    font_name=span['font'],
                                    bbox=span['bbox'],
                                    page_num=i,
                                    is_italic=bool(span['flags'] & 2**1)
                                )
                                blocks.append(block)
    except Exception as e:
        print(f'Error: {e}')
    return blocks, page_width

text_blocks, page_width = extract_text_blocks_from_pdf('input/file02.pdf')

print("Looking for 18pt text blocks:")
for block in text_blocks:
    if abs(block.font_size - 18.0) < 0.1:
        print(f'Text: "{block.text}"')
        print(f'Font size: {block.font_size}pt')
        print(f'Bold: {block.is_bold}')
        print(f'Page: {block.page_num}')
        print(f'Position: x={block.x_position}, y={block.y_position}')
        print(f'Font name: {block.font_name}')
        print()
