import re
import statistics
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict


class TextBlock:
    """Represents a block of text with its formatting properties."""
    
    def __init__(self, text: str, font_size: float, font_name: str, 
                 bbox: Tuple[float, float, float, float], page_num: int):
        self.text = text.strip()
        self.font_size = font_size
        self.font_name = font_name
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.page_num = page_num
        self.is_bold = self._detect_bold()
        self.is_all_caps = text.isupper() and len(text) > 1
        self.heading_score = 0.0
        
    def _detect_bold(self) -> bool:
        """Detect if text is bold based on font name."""
        bold_indicators = ['bold', 'black', 'heavy', 'demi', 'semi']
        font_lower = self.font_name.lower()
        return any(indicator in font_lower for indicator in bold_indicators)
    
    def get_indentation(self) -> float:
        """Get the left margin/indentation of the text block."""
        return self.bbox[0]
    
    def get_center_x(self) -> float:
        """Get the horizontal center of the text block."""
        return (self.bbox[0] + self.bbox[2]) / 2
    
    def is_centered(self, page_width: float, tolerance: float = 50) -> bool:
        """Check if text is approximately centered on the page."""
        center_x = self.get_center_x()
        page_center = page_width / 2
        return abs(center_x - page_center) < tolerance


class DocumentAnalyzer:
    """Analyzes document structure and extracts headings."""
    
    def __init__(self):
        self.text_blocks: List[TextBlock] = []
        self.baseline_font_size = 0.0
        self.baseline_font_name = ""
        self.page_width = 0.0
        
        # Regex patterns for numbering
        self.numbering_patterns = [
            re.compile(r'^\d+\.'),                        # "1." or "1. Introduction"
            re.compile(r'^\d+\.\d+'),                     # "1.1" or "1.1 Overview"
            re.compile(r'^\d+\.\d+\.\d+'),                # "1.1.1" or "1.1.1 Details"
            re.compile(r'^Chapter\s+\d+', re.IGNORECASE), # "Chapter 1"
            re.compile(r'^Section\s+[A-Z]', re.IGNORECASE), # "Section A"
            re.compile(r'^[A-Z]\.'),                      # "A." or "A. Point"
            re.compile(r'^[IVX]+\.'),                     # Roman numerals "I." or "I. Introduction"
        ]
    
    def add_text_block(self, text_block: TextBlock):
        """Add a text block to the analyzer."""
        if text_block.text and len(text_block.text.strip()) > 0:
            self.text_blocks.append(text_block)
    
    def calculate_baseline(self):
        """Calculate the baseline font size and style (most common body text)."""
        if not self.text_blocks:
            return
            
        # Filter out very short text (likely not body text)
        body_candidates = [
            block for block in self.text_blocks 
            if len(block.text) > 20 and not block.is_all_caps
        ]
        
        if not body_candidates:
            body_candidates = self.text_blocks
        
        # Find most common font size
        font_sizes = [block.font_size for block in body_candidates]
        if font_sizes:
            self.baseline_font_size = statistics.mode(font_sizes)
        
        # Find most common font name
        font_names = [block.font_name for block in body_candidates]
        if font_names:
            font_counter = Counter(font_names)
            self.baseline_font_name = font_counter.most_common(1)[0][0]
    
    def detect_numbering_pattern(self, text: str) -> Tuple[bool, int]:
        """
        Detect if text follows a numbering pattern.
        Returns (has_pattern, hierarchy_level)
        """
        text_start = text[:20].strip()
        
        # Check for multi-level numbering first (most specific)
        if re.match(r'^\d+\.\d+\.\d+', text_start):
            return True, 3
        elif re.match(r'^\d+\.\d+', text_start):
            return True, 2
        elif re.match(r'^\d+\.', text_start):
            return True, 1
        
        # Check other patterns
        for i, pattern in enumerate(self.numbering_patterns[3:], 1):  # Skip the first 3 we already checked
            if pattern.match(text_start):
                return True, 1  # Most other patterns are level 1
        
        return False, 0
    
    def calculate_heading_score(self, block: TextBlock) -> float:
        """
        Calculate a heading score for a text block based on multiple factors.
        Higher score = more likely to be a heading.
        """
        score = 0.0
        
        # Font size factor (most important)
        if self.baseline_font_size > 0:
            size_ratio = block.font_size / self.baseline_font_size
            if size_ratio > 1.2:  # At least 20% larger
                score += (size_ratio - 1) * 50
        
        # Bold font factor
        if block.is_bold:
            score += 20
        
        # All caps factor
        if block.is_all_caps and len(block.text) < 100:
            score += 15
        
        # Short text factor (headings are usually concise)
        if len(block.text) < 100:
            score += 10
        elif len(block.text) > 200:
            score -= 10
        
        # Numbering pattern factor
        has_numbering, level = self.detect_numbering_pattern(block.text)
        if has_numbering:
            score += 30  # Increased from 25
            # Give bonus for numbered patterns with proper hierarchy levels
            if level == 2:
                score += 5  # 1.1 patterns
            elif level == 3:
                score += 10  # 1.1.1 patterns
        
        # Position factors
        if hasattr(self, 'page_width') and self.page_width > 0:
            if block.is_centered(self.page_width):
                score += 15
        
        # Font name change factor
        if block.font_name != self.baseline_font_name:
            score += 10
        
        # First page factor (title detection)
        if block.page_num == 1:
            score += 5
        
        return score
    
    def analyze_document(self):
        """Analyze the entire document and score all text blocks."""
        self.calculate_baseline()
        
        for block in self.text_blocks:
            block.heading_score = self.calculate_heading_score(block)
    
    def find_title(self) -> Optional[TextBlock]:
        """Find the document title (highest scoring block on first page)."""
        first_page_blocks = [
            block for block in self.text_blocks 
            if block.page_num == 1 and len(block.text) > 5
        ]
        
        if not first_page_blocks:
            return None
        
        # Return the highest scoring block on the first page
        return max(first_page_blocks, key=lambda x: x.heading_score)
    
    def extract_headings(self, min_score: float = 25.0) -> List[TextBlock]:
        """Extract heading blocks based on their scores."""
        headings = []
        
        for block in self.text_blocks:
            # Additional filters to reduce false positives
            if (block.heading_score >= min_score and 
                len(block.text.strip()) > 2 and  # Minimum length
                len(block.text) < 150):  # Maximum length for headings (reduced from 200)
                
                # Skip very long sentences (likely body text)
                sentence_count = block.text.count('.') + block.text.count('!') + block.text.count('?')
                word_count = len(block.text.split())
                
                # More restrictive filtering
                if (sentence_count <= 1 and word_count <= 15) or block.heading_score > 50:
                    headings.append(block)
        
        # Sort by page number, then by position on page
        headings.sort(key=lambda x: (x.page_num, x.bbox[1]))
        
        return headings
    
    def assign_heading_levels(self, headings: List[TextBlock]) -> List[Dict]:
        """Assign H1/H2/H3 levels to headings and return structured output."""
        if not headings:
            return []
        
        # Group headings by similar properties
        clusters = self._cluster_headings(headings)
        
        # Sort clusters by prominence (font size, then score)
        clusters.sort(key=lambda cluster: (
            -max(h.font_size for h in cluster),
            -max(h.heading_score for h in cluster)
        ))
        
        # Assign levels
        result = []
        level_map = {0: "H1", 1: "H2", 2: "H3"}
        
        for heading in headings:
            # Find which cluster this heading belongs to
            cluster_index = 0
            for i, cluster in enumerate(clusters):
                if heading in cluster:
                    cluster_index = i
                    break
            
            # Check for numbering pattern override
            has_numbering, pattern_level = self.detect_numbering_pattern(heading.text)
            if has_numbering and pattern_level > 0:
                level = level_map.get(pattern_level - 1, "H3")
            else:
                level = level_map.get(min(cluster_index, 2), "H3")
            
            result.append({
                "level": level,
                "text": heading.text,
                "page": heading.page_num
            })
        
        return result
    
    def _cluster_headings(self, headings: List[TextBlock]) -> List[List[TextBlock]]:
        """Group headings into clusters based on similar properties."""
        if not headings:
            return []
        
        clusters = []
        tolerance = 2.0  # Font size tolerance for clustering
        
        for heading in headings:
            placed = False
            
            # Try to place in existing cluster
            for cluster in clusters:
                representative = cluster[0]
                if (abs(heading.font_size - representative.font_size) <= tolerance and
                    heading.is_bold == representative.is_bold):
                    cluster.append(heading)
                    placed = True
                    break
            
            # Create new cluster if not placed
            if not placed:
                clusters.append([heading])
        
        return clusters
