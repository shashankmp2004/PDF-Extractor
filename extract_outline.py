#!/usr/bin/env python3
"""
PDF Outline Extractor

This script extracts hierarchical structure (title, headings) from PDF files
and outputs clean JSON files with the document outline.
"""

import os
import json
import time
import fitz  # PyMuPDF
import multiprocessing as mp
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.analysis import DocumentAnalyzer, TextBlock


class PDFOutlineExtractor:
    """Main class for extracting PDF outlines."""
    
    def __init__(self):
        self.input_dir = "/app/input"
        self.output_dir = "/app/output"
        
    def extract_text_blocks_from_pdf(self, pdf_path: str) -> List[TextBlock]:
        """Extract text blocks with metadata from a PDF file."""
        text_blocks = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_width = page.rect.width
                
                # Get text blocks with formatting information
                blocks = page.get_text("dict")
                
                for block in blocks["blocks"]:
                    if "lines" in block:  # Text block
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"]
                                if text.strip():  # Only non-empty text
                                    bbox = span["bbox"]
                                    font_size = span["size"]
                                    font_name = span["font"]
                                    
                                    text_block = TextBlock(
                                        text=text,
                                        font_size=font_size,
                                        font_name=font_name,
                                        bbox=bbox,
                                        page_num=page_num + 1
                                    )
                                    text_blocks.append(text_block)
            
            doc.close()
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")
            return []
        
        return text_blocks
    
    def process_single_pdf(self, pdf_path: str) -> Optional[Dict]:
        """Process a single PDF file and extract its outline."""
        print(f"Processing: {os.path.basename(pdf_path)}")
        start_time = time.time()
        
        # Extract text blocks
        text_blocks = self.extract_text_blocks_from_pdf(pdf_path)
        
        if not text_blocks:
            print(f"No text blocks found in {pdf_path}")
            return None
        
        # Initialize analyzer
        analyzer = DocumentAnalyzer()
        
        # Add text blocks to analyzer
        for block in text_blocks:
            analyzer.add_text_block(block)
        
        # Analyze document
        analyzer.analyze_document()
        
        # Find title
        title_block = analyzer.find_title()
        title = title_block.text if title_block else "Untitled Document"
        
        # Extract headings
        headings = analyzer.extract_headings(min_score=25.0)
        
        # Assign levels and create outline
        outline = analyzer.assign_heading_levels(headings)
        
        # Create final JSON structure
        result = {
            "title": title,
            "outline": outline
        }
        
        processing_time = time.time() - start_time
        print(f"Processed {os.path.basename(pdf_path)} in {processing_time:.2f} seconds")
        print(f"Found title: '{title}'")
        print(f"Found {len(outline)} headings")
        
        return result
    
    def save_json_output(self, result: Dict, output_path: str):
        """Save the extracted outline to a JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Saved: {output_path}")
        except Exception as e:
            print(f"Error saving {output_path}: {str(e)}")
    
    def process_pdf_worker(self, pdf_file: str) -> None:
        """Worker function for processing a single PDF (for multiprocessing)."""
        pdf_path = os.path.join(self.input_dir, pdf_file)
        
        # Generate output filename
        output_filename = Path(pdf_file).stem + ".json"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Process PDF
        result = self.process_single_pdf(pdf_path)
        
        if result:
            self.save_json_output(result, output_path)
        else:
            print(f"Failed to process {pdf_file}")
    
    def run_batch_processing(self):
        """Process all PDF files in the input directory."""
        print("=== PDF Outline Extractor ===")
        print(f"Input directory: {self.input_dir}")
        print(f"Output directory: {self.output_dir}")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Find all PDF files
        pdf_files = []
        if os.path.exists(self.input_dir):
            pdf_files = [f for f in os.listdir(self.input_dir) 
                        if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print("No PDF files found in input directory!")
            return
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        start_time = time.time()
        
        # Determine number of processes (use available CPUs, max 8)
        num_processes = min(mp.cpu_count(), 8, len(pdf_files))
        print(f"Using {num_processes} processes")
        
        if num_processes > 1 and len(pdf_files) > 1:
            # Parallel processing
            with mp.Pool(processes=num_processes) as pool:
                pool.map(self.process_pdf_worker, pdf_files)
        else:
            # Sequential processing
            for pdf_file in pdf_files:
                self.process_pdf_worker(pdf_file)
        
        total_time = time.time() - start_time
        print(f"\n=== Processing Complete ===")
        print(f"Processed {len(pdf_files)} files in {total_time:.2f} seconds")
        print(f"Average time per file: {total_time/len(pdf_files):.2f} seconds")


def main():
    """Main entry point."""
    extractor = PDFOutlineExtractor()
    
    # Check if running in development mode (local testing)
    if len(sys.argv) > 1 and sys.argv[1] == "--dev":
        # Development mode - use local paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        extractor.input_dir = os.path.join(current_dir, "input")
        extractor.output_dir = os.path.join(current_dir, "output")
        print("Running in development mode")
    
    extractor.run_batch_processing()


if __name__ == "__main__":
    main()
