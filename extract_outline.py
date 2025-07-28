import os
import json
import time
import fitz  
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
                                    page_num=i,
                                    is_italic=span["italic"]
                                ))
            doc.close()
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
        return blocks, page_width

    def process_single_pdf(self, pdf_path: str) -> Optional[Dict]:
        print(f"Processing: {os.path.basename(pdf_path)}")
        text_blocks, page_width = self.extract_text_blocks_from_pdf(pdf_path)
        if not text_blocks:
            return None

        analyzer = DocumentAnalyzer()
        analyzer.set_page_width(page_width)
        for b in text_blocks:
            analyzer.add_text_block(b)

        title, outline = analyzer.analyze_document()
        return {"title": title, "outline": outline}

    def save_json_output(self, result: Dict, output_path: str):
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Saved: {output_path}")
        except Exception as e:
            print(f"Error saving output: {e}")

    def process_pdf_worker(self, pdf_file: str):
        pdf_path = os.path.join(self.input_dir, pdf_file)
        output_path = os.path.join(self.output_dir, Path(pdf_file).stem + '.json')
        result = self.process_single_pdf(pdf_path)
        if result:
            self.save_json_output(result, output_path)

    def run_batch_processing(self):
        os.makedirs(self.output_dir, exist_ok=True)
        pdf_files = [f for f in os.listdir(self.input_dir) if f.lower().endswith(".pdf")]
        if not pdf_files:
            print("No PDFs found")
            return
        print(f"Found {len(pdf_files)} PDF files")
        num_processes = min(mp.cpu_count(), 8, len(pdf_files))
        with mp.Pool(processes=num_processes) as pool:
            pool.map(self.process_pdf_worker, pdf_files)


def main():
    extractor = PDFOutlineExtractor()
    if len(sys.argv) > 1 and sys.argv[1] == '--dev':
        extractor.input_dir = os.path.join(os.path.dirname(__file__), 'input')
        extractor.output_dir = os.path.join(os.path.dirname(__file__), 'output')
    extractor.run_batch_processing()


if __name__ == "__main__":
    main()
