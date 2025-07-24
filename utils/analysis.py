import re
import statistics
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict


class TextBlock:
    """Represents a block of text with its formatting and positional properties."""
    
    def __init__(self, text: str, font_size: float, font_name: str, 
                 bbox: Tuple[float, float, float, float], page_num: int, is_italic: bool):
        self.text = text.strip()
        self.font_size = font_size
        self.font_name = font_name
        self.bbox = bbox
        self.page_num = page_num
        self.is_italic = is_italic
        
        # Extract positional properties from bbox
        self.x_position = bbox[0]
        self.y_position = bbox[1]
        
        # Determine other style properties
        self.is_bold = self._detect_bold()
        self.is_all_caps = text.isupper() and len(text) > 5
        
        # This will be calculated in the second pass
        self.heading_score = 0.0
        
    def _detect_bold(self) -> bool:
        """Detect if text is bold based on font name."""
        bold_indicators = ['bold', 'black', 'heavy', 'demi', 'semi']
        font_lower = self.font_name.lower()
        return any(indicator in font_lower for indicator in bold_indicators)


class DocumentAnalyzer:
    """Analyzes document structure using a two-pass algorithm."""
    
    def __init__(self):
        self.text_blocks: List[TextBlock] = []
        
        # Global analysis results (from first pass)
        self.body_font_size = 0.0
        self.body_font_name = ""
        self.unique_font_sizes = []
        
        # Regex for numbering patterns
        self.numbering_patterns = [
            re.compile(r'^\d+\.\s'),        # "1. "
            re.compile(r'^\d+\.\d+'),       # "1.1"
            re.compile(r'^\d+\.\d+\.\d+'),  # "1.1.1"
            re.compile(r'^Chapter\s+\d+', re.IGNORECASE),
            re.compile(r'^Section\s+[A-Z]', re.IGNORECASE),
            re.compile(r'^[A-Z]\.'),
            re.compile(r'^[IVX]+\.'),
        ]
    
    def add_text_block(self, text_block: TextBlock):
        """Add a text block to the analyzer."""
        if text_block.text:
            self.text_blocks.append(text_block)
    
    def global_analysis_pass(self):
        """
        First pass: Analyze the entire document to establish a baseline style.
        """
        if not self.text_blocks:
            return
        
        # Find the most common font size and name (body text style)
        font_styles = [(block.font_size, block.font_name) for block in self.text_blocks if len(block.text) > 20]
        if font_styles:
            style_counter = Counter(font_styles)
            most_common_style = style_counter.most_common(1)[0][0]
            self.body_font_size = most_common_style[0]
            self.body_font_name = most_common_style[1]
        
        # Identify all unique font sizes used in the document
        all_font_sizes = {block.font_size for block in self.text_blocks}
        self.unique_font_sizes = sorted(list(all_font_sizes), reverse=True)
    
    def classification_pass(self) -> List[TextBlock]:
        """
        Second pass: Classify each text block and calculate a heading score.
        """
        heading_candidates = []
        
        for i, block in enumerate(self.text_blocks):
            score = 0.0
            text = block.text.strip()

            # Filter out extremely short text unless it's a clear numbering
            if len(text) <= 2 and not self._matches_numbering_pattern(text):
                continue
            
            # Rule 1: Size relative to body text
            if self.body_font_size > 0 and block.font_size > self.body_font_size:
                score += (block.font_size - self.body_font_size) * 2
            
            # Rule 2: Boldness is a strong signal
            if block.is_bold:
                score += 10
            
            # Rule 3: ALL CAPS is another strong signal
            if block.is_all_caps:
                score += 8
            
            # Rule 4: Numbering patterns are very reliable
            if self._matches_numbering_pattern(text):
                score += 15
            
            # Rule 5: Extra space above the line
            if i > 0:
                prev_block = self.text_blocks[i-1]
                if self._has_extra_space_above(block, prev_block):
                    score += 5
            
            # Add block to candidates if it has a meaningful score
            if score > 18:  # Increased threshold to be more selective
                block.heading_score = score
                heading_candidates.append(block)
        
        return heading_candidates
    
    def _matches_numbering_pattern(self, text: str) -> bool:
        """Check if text matches any of the numbering patterns."""
        text_start = text.strip()[:20]
        return any(pattern.match(text_start) for pattern in self.numbering_patterns)
    
    def _has_extra_space_above(self, current_block: TextBlock, prev_block: TextBlock) -> bool:
        """Check for significant vertical spacing between blocks."""
        if current_block.page_num != prev_block.page_num:
            return True  # New page implies space
        
        vertical_gap = current_block.y_position - prev_block.bbox[3]  # y0_current - y1_prev
        
        # A gap larger than the typical line height is considered extra space
        typical_line_height = self.body_font_size * 1.2 if self.body_font_size > 0 else 12.0
        return vertical_gap > typical_line_height
    
    def assign_hierarchy(self, heading_candidates: List[TextBlock], is_form: bool = False) -> Tuple[Optional[TextBlock], List[Dict]]:
        """Assign title and H1/H2/H3 levels to heading candidates, with special handling for forms."""
        # --- Improved Title Finding Logic ---
        title_block = self._find_best_title()
        
        # If it's a form, we return the title but an empty outline.
        if is_form:
            return title_block, []

        # Remove title from heading candidates if found
        if title_block:
            heading_candidates = [h for h in heading_candidates if h != title_block]

        # --- Hierarchy Assignment for Outline ---
        if not heading_candidates:
            return title_block, []

        heading_candidates.sort(key=lambda b: (b.page_num, b.y_position))

        clusters = defaultdict(list)
        for heading in heading_candidates:
            cluster_key = (round(heading.font_size), heading.is_bold)
            clusters[cluster_key].append(heading)
        
        sorted_clusters = sorted(clusters.keys(), key=lambda x: x[0], reverse=True)
        
        level_map = {0: "H1", 1: "H2", 2: "H3"}
        
        outline = []
        for heading in heading_candidates:
            cluster_key = (round(heading.font_size), heading.is_bold)
            
            try:
                rank = sorted_clusters.index(cluster_key)
            except ValueError:
                rank = len(level_map) - 1
            
            level = level_map.get(min(rank, len(level_map) - 1), "H3")
            
            if self._matches_numbering_pattern(heading.text):
                text_start = heading.text.strip()
                dots = text_start.split()[0].count('.')
                if dots == 1: level = "H2"
                elif dots >= 2: level = "H3"

            if heading.heading_score < 25 and not self._matches_numbering_pattern(heading.text):
                continue

            outline.append({
                "level": level,
                "text": heading.text,
                "page": heading.page_num,
            })
        
        return title_block, outline

    def _find_best_title(self) -> Tuple[Optional[TextBlock], bool]:
        """Find the best title candidate and determine if the document is a form."""
        first_page_blocks = [b for b in self.text_blocks if b.page_num == 0 and len(b.text.strip()) > 1]
        if not first_page_blocks:
            return None, False

        # Document type detection
        first_page_text = " ".join(b.text.lower() for b in first_page_blocks)
        form_indicators = ['application', 'form', 'name:', 'date:', 'designation:', 's.no']
        is_form = sum(1 for indicator in form_indicators if indicator in first_page_text) >= 2

        title_candidates = []
        for block in first_page_blocks:
            score = 0
            text_lower = block.text.lower()
            
            if block.y_position < 200: score += 30
            if self.body_font_size > 0 and block.font_size > self.body_font_size:
                score += (block.font_size - self.body_font_size) * 2
            if block.is_bold: score += 15
            if len(block.text) < 4: score -= 20
            if len(block.text) > 150: score -= 10
            if any(kw in text_lower for kw in ['page', 'confidential', 'date:']):
                score -= 50
            
            if score > 5:
                title_candidates.append((block, score))

        if not title_candidates:
            return None, is_form

        title_candidates.sort(key=lambda x: x[1], reverse=True)
        best_candidate = title_candidates[0][0]

        # Refined Merging Logic
        if not is_form:
            merged_title_text = self._merge_adjacent_title_lines(best_candidate)
            # Clean up repetitive text common in logos/headers
            words = merged_title_text.split()
            if len(words) > 2 and words[0] == words[1] and words[0] == words[2]:
                 merged_title_text = " ".join(words[2:])
            best_candidate.text = merged_title_text
        
        return best_candidate, is_form
    
    def _merge_adjacent_title_lines(self, title_block: TextBlock) -> str:
        """Merge a title block with adjacent blocks if they share similar styles."""
        merged_text = [title_block.text]
        
        try:
            start_index = self.text_blocks.index(title_block)
        except ValueError:
            return title_block.text

        for i in range(start_index + 1, min(start_index + 3, len(self.text_blocks))):
            next_block = self.text_blocks[i]
            
            if next_block.page_num != title_block.page_num:
                break

            font_size_diff = abs(next_block.font_size - title_block.font_size)
            vertical_gap = next_block.y_position - self.text_blocks[i-1].bbox[3]
            horizontal_diff = abs(next_block.x_position - title_block.x_position)

            if font_size_diff < 1.0 and vertical_gap < (title_block.font_size * 1.2) and horizontal_diff < 20:
                merged_text.append(next_block.text)
            else:
                break

        return " ".join(merged_text).replace("  ", " ")
    
    def analyze_document(self) -> Tuple[Optional[str], List[Dict]]:
        """Run the full two-pass analysis and return the final outline."""
        self.global_analysis_pass()
        heading_candidates = self.classification_pass()
        
        title_block, is_form = self._find_best_title()
        
        _, outline = self.assign_hierarchy(heading_candidates, is_form=is_form)
        
        title_text = title_block.text if title_block else ""
        
        return title_text, outline
