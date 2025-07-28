import os
import json
import time
import re
import fitz  # PyMuPDF
import multiprocessing as mp
from pathlib import Path
from typing import List, Dict, Optional
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.analysis_new import DocumentAnalyzer, TextBlock

class PDFOutlineExtractor:
    def __init__(self):
        self.input_dir = "input"
        self.output_dir = "output"

    def extract_text_blocks_from_pdf(self, pdf_path: str):
        """Enhanced PDF text extraction (PyMuPDF only)"""
        blocks = []
        page_width = 0.0
        
        try:
            doc = fitz.open(pdf_path)
            for i, page in enumerate(doc):
                if i == 0:
                    page_width = page.rect.width
                
                # PyMuPDF extraction with enhanced processing
                blocks.extend(self._extract_pymupdf_blocks(page, i))
            
            doc.close()
                    
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            
        return blocks, page_width

    def _extract_pymupdf_blocks(self, page, page_num):
        """Extract text blocks using PyMuPDF with enhanced processing"""
        blocks = []
        
        for b in page.get_text("dict")["blocks"]:
            if "lines" in b:
                for line in b["lines"]:
                    merged_spans = []
                    current_text = ""
                    current_bbox = None
                    current_font = None
                    current_size = None
                    current_italic = False
                    
                    for span in line["spans"]:
                        if not span["text"].strip():
                            continue
                            
                        if current_font is None:
                            current_text = span["text"]
                            current_bbox = span["bbox"]
                            current_font = span["font"]
                            current_size = span["size"]
                            current_italic = 'italic' in span["font"].lower()
                        elif (span["font"] == current_font and 
                              abs(span["size"] - current_size) <= 1.0 and 
                              abs(span["bbox"][1] - current_bbox[1]) <= max(current_size * 0.2, 2)):
                            
                            x_gap = span["bbox"][0] - current_bbox[2]
                            
                            if x_gap < 0:
                                current_text += span["text"]
                            elif x_gap <= current_size * 0.3:
                                current_text += span["text"]
                            elif x_gap <= current_size * 1.5:
                                current_text += " " + span["text"]
                            else:
                                if current_text.strip():
                                    merged_spans.append({
                                        "text": current_text,
                                        "bbox": current_bbox,
                                        "font": current_font,
                                        "size": current_size,
                                        "italic": current_italic
                                    })
                                current_text = span["text"]
                                current_bbox = span["bbox"]
                                current_font = span["font"]
                                current_size = span["size"]
                                current_italic = 'italic' in span["font"].lower()
                                continue
                            
                            current_bbox = (
                                min(current_bbox[0], span["bbox"][0]),
                                min(current_bbox[1], span["bbox"][1]),
                                max(current_bbox[2], span["bbox"][2]),
                                max(current_bbox[3], span["bbox"][3])
                            )
                        else:
                            if current_text.strip():
                                merged_spans.append({
                                    "text": current_text,
                                    "bbox": current_bbox,
                                    "font": current_font,
                                    "size": current_size,
                                    "italic": current_italic
                                })
                            
                            current_text = span["text"]
                            current_bbox = span["bbox"]
                            current_font = span["font"]
                            current_size = span["size"]
                            current_italic = 'italic' in span["font"].lower()
                    
                    if current_text.strip():
                        merged_spans.append({
                            "text": current_text,
                            "bbox": current_bbox,
                            "font": current_font,
                            "size": current_size,
                            "italic": current_italic
                        })
                    
                    for span in merged_spans:
                        blocks.append(TextBlock(
                            text=span["text"],
                            font_size=span["size"],
                            font_name=span["font"],
                            bbox=span["bbox"],
                            page_num=page_num,
                            is_italic=span["italic"]
                        ))
        
        return blocks

    def process_single_pdf(self, pdf_path: str) -> Optional[Dict]:
        print(f"Processing: {os.path.basename(pdf_path)}")
        text_blocks, page_width = self.extract_text_blocks_from_pdf(pdf_path)
        if not text_blocks:
            print(f"No text blocks found in {pdf_path}")
            return None

        analyzer = DocumentAnalyzer()
        analyzer.set_page_width(page_width)
        
        for block in text_blocks:
            analyzer.add_text_block(block)
        
        title, outline = analyzer.analyze_document()
        
        return {
            "filename": os.path.basename(pdf_path),
            "title": title,
            "outline": outline
        }

    def process_all_pdfs(self):
        pdf_files = list(Path(self.input_dir).glob("*.pdf"))
        if not pdf_files:
            print("No PDF files found in input directory")
            return

        print(f"Found {len(pdf_files)} PDF files")
        
        with mp.Pool() as pool:
            results = pool.map(self.process_single_pdf, [str(f) for f in pdf_files])
        
        for result in results:
            if result:
                filename = result["filename"]
                output_file = Path(self.output_dir) / f"{Path(filename).stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"Generated: {output_file}")

if __name__ == "__main__":
    start_time = time.time()
    extractor = PDFOutlineExtractor()
    extractor.process_all_pdfs()  
    end_time = time.time()
    print(f"Total processing time: {end_time - start_time:.2f} seconds")
