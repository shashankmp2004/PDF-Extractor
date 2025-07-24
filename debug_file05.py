import fitz

# Analyze file02 structure first
print('=== FILE02 TEXT BLOCKS (first 25) ===')
doc = fitz.open('input/file02.pdf')

count = 0
for page_num in range(min(2, len(doc))):  # Only first 2 pages
    page = doc[page_num]
    blocks = page.get_text("dict")["blocks"]
    
    for block_idx, block in enumerate(blocks):
        if "lines" in block:
            for line_idx, line in enumerate(block["lines"]):
                for span_idx, span in enumerate(line["spans"]):
                    text = span["text"].strip()
                    if text and count < 25:
                        print(f'"{text}" | Font: {span["font"]} | Size: {span["size"]:.1f} | Bold: {bool(span["flags"] & 2**4)} | Page: {page_num} | Y: {span["bbox"][1]:.1f}')
                        count += 1

doc.close()
