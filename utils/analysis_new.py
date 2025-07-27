import re
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict

class TextBlock:
    def __init__(self, text: str, font_size: float, font_name: str, 
                 bbox: Tuple[float, float, float, float], page_num: int, is_italic: bool = False):
        self.text = text.strip()
        self.font_size = font_size
        self.font_name = font_name
        self.bbox = bbox
        self.page_num = page_num
        self.is_italic = is_italic

        self.x_position = bbox[0]
        self.y_position = bbox[1]
        self.is_bold = self._detect_bold()
        self.text_case = self._categorize_text_case()
        self.char_count = len(self.text)
        self.numbering_pattern = self._detect_numbering_pattern()

        self.space_above = 0.0
        self.is_isolated = False
        self.is_centered = False
        self.heading_score = 0.0

    def _detect_bold(self) -> bool:
        return any(k in self.font_name.lower() for k in ['bold', 'black', 'heavy', 'demi', 'semi'])

    def _categorize_text_case(self) -> str:
        if self.text.isupper(): return "UPPER"
        if self.text.istitle(): return "Title Case"
        return "Lower"

    def _detect_numbering_pattern(self) -> Optional[str]:
        head = self.text[:20]
        patterns = [(r'\d+\.\d+\.\d+', 'x.y.z.'), (r'\d+\.\d+', 'x.y.'), (r'\d+\.', 'x.'), (r'[A-Z]\.', 'A.'), (r'[IVX]+\.', 'I.')]
        for pat, tag in patterns:
            if re.match(pat, head): return tag
        return None


class DocumentAnalyzer:
    def __init__(self):
        self.text_blocks: List[TextBlock] = []
        self.page_width = 0.0
        self.baseline_font_size = 0.0

    def set_page_width(self, width: float):
        self.page_width = width

    def add_text_block(self, block: TextBlock):
        self.text_blocks.append(block)

    def analyze_document(self):
        self._pass1()
        self._pass2()
        return self._pass3()

    def _pass1(self):
        for i, b in enumerate(self.text_blocks):
            if i > 0 and b.page_num == self.text_blocks[i-1].page_num:
                b.space_above = b.y_position - self.text_blocks[i-1].bbox[3]
            b.is_centered = abs((self.page_width/2) - (b.bbox[0] + b.bbox[2])/2) < self.page_width * 0.2

    def _pass2(self):
        # Get all blocks for baseline calculation, excluding very small text
        body = [b for b in self.text_blocks if b.char_count > 10 and b.font_size >= 8] or self.text_blocks
        sizes = [b.font_size for b in body]
        self.baseline_font_size = Counter(sizes).most_common(1)[0][0]
        
        # Calculate font size distribution for better heading detection
        size_counter = Counter(sizes)
        sorted_sizes = sorted(size_counter.keys(), reverse=True)
        
        # Identify distinct heading size tiers
        # Look for natural breaks in font sizes to identify heading levels
        size_tiers = []
        for i, size in enumerate(sorted_sizes):
            if size >= self.baseline_font_size * 1.15:  # Must be meaningfully larger than body text
                # Check if this size appears frequently enough to be a heading level
                # Or appears on content pages (not title page)
                blocks_with_size = [b for b in body if b.font_size == size]
                content_page_blocks = [b for b in blocks_with_size if b.page_num > 0]  # Exclude title page
                
                if (size_counter[size] >= 2 or size >= self.baseline_font_size * 1.5) and len(content_page_blocks) > 0:
                    size_tiers.append(size)
        
        # Store size tiers for use in clustering
        # If largest font is significantly bigger than second (likely title), exclude it from heading tiers
        if len(size_tiers) >= 2 and size_tiers[0] > size_tiers[1] * 1.3:
            self.heading_size_tiers = size_tiers[1:5]  # Skip likely title font, max 4 heading levels
        else:
            self.heading_size_tiers = size_tiers[:4]  # Max 4 heading levels from font size
        
        for b in self.text_blocks:
            score = 0
            
            # Enhanced font size scoring based on tiers
            size_ratio = b.font_size / self.baseline_font_size
            if b.font_size in self.heading_size_tiers:
                # Bonus for being in a recognized heading size tier
                tier_index = self.heading_size_tiers.index(b.font_size)
                score += 25 - (tier_index * 3)  # H1 gets 25, H2 gets 22, etc.
            elif size_ratio >= 2.0: score += 20  # Very large
            elif size_ratio >= 1.5: score += 15  # Large
            elif size_ratio >= 1.2: score += 10  # Medium-large
            elif size_ratio >= 1.1: score += 5   # Slightly large
            
            # Bold text bonus - higher for larger fonts
            if b.is_bold:
                if size_ratio >= 1.3: score += 12
                else: score += 8
            
            # Numbering pattern bonus
            if b.numbering_pattern:
                score += 18  # Strong indicator of heading
            
            # Text case bonus
            if b.text_case == "UPPER": score += 6
            elif b.text_case == "Title Case": score += 4
            
            # Spacing bonus
            if b.space_above > self.baseline_font_size * 1.5: score += 10
            
            # Centered text bonus (for titles)
            if b.is_centered and size_ratio >= 1.2: score += 8
            
            # Length penalties and bonuses
            if b.char_count < 4: score -= 8
            elif 4 <= b.char_count <= 50: score += 2  # Good heading length
            elif b.char_count > 100: score -= 5  # Too long for typical heading
            
            # Body text penalties
            if b.font_size < self.baseline_font_size * 0.95: score -= 8
            
            b.heading_score = score

    def _pass3(self):
        # Check if this is a single-page poster-like document
        total_pages = len(set(b.page_num for b in self.text_blocks))
        is_poster = total_pages == 1
        
        # Filter heading candidates: need a letter, sufficient score, and either numbered or larger font
        candidates = []
        for b in self.text_blocks:
            # Basic filters - for posters, also allow punctuation
            if is_poster:
                if b.heading_score < 20 or not re.search('[A-Za-z!]', b.text):
                    continue
            else:
                if b.heading_score < 20 or not re.search('[A-Za-z]', b.text):
                    continue
            # Exclude version metadata
            if re.match(r'Version \d+\.\d+', b.text, re.I):
                continue
            # For posters, be more selective - only very large fonts or very high scores
            if is_poster:
                # Only consider text that's significantly larger or has very high scores
                if b.font_size < self.baseline_font_size * 1.3 and b.heading_score < 30:
                    continue
                # Skip small text snippets that are likely address/details, but allow single letters/symbols
                if b.char_count < 8 and not (b.font_size > self.baseline_font_size * 1.5) and b.char_count > 1:
                    continue
            else:
                # Ensure either numbered or sufficiently larger font
                if not b.numbering_pattern and b.font_size < self.baseline_font_size * 1.05:
                    continue
            candidates.append(b)

        # Enhanced title reconstruction for fragmented text
        first_page_blocks = [b for b in self.text_blocks if b.page_num == 0]
        title = ""
        title_blocks = []
        
        if first_page_blocks:
            # Sort by font size descending, then by vertical position
            sorted_fp = sorted(first_page_blocks, key=lambda b: (-b.font_size, b.y_position))
            
            if not sorted_fp:
                return title, []
                
            max_fs = sorted_fp[0].font_size
            total_pages = len(set(b.page_num for b in self.text_blocks))
            
            # For multi-page documents, look for title elements
            if total_pages > 1:
                # Get all blocks with large fonts that could be title components
                large_font_threshold = max_fs * 0.85
                title_candidates = [b for b in sorted_fp if b.font_size >= large_font_threshold]
                
                # Group title candidates by Y position (handling overlapping text)
                y_groups = {}
                for candidate in title_candidates:
                    # Group by Y position with tolerance for overlapping spans
                    found_group = False
                    for existing_y in y_groups.keys():
                        if abs(candidate.y_position - existing_y) <= max(candidate.font_size * 0.15, 3):
                            y_groups[existing_y].append(candidate)
                            found_group = True
                            break
                    
                    if not found_group:
                        y_groups[candidate.y_position] = [candidate]
                
                # Process each Y group to merge overlapping/fragmented text
                title_lines = []
                for y_pos, group in sorted(y_groups.items()):
                    # Sort group by X position
                    group.sort(key=lambda x: x.x_position)
                    
                    # Merge overlapping or adjacent spans in this line
                    merged_text = ""
                    last_end_x = -1000
                    
                    for block in group:
                        text = block.text.strip()
                        start_x = block.x_position
                        
                        # Handle overlapping spans (common in fragmented PDFs)
                        if start_x < last_end_x + block.font_size * 0.2:
                            # This span overlaps or is very close to the previous one
                            # Check if it's a duplicate or continuation
                            if text in merged_text or merged_text.endswith(text[:3]):
                                # Skip duplicate or already included text
                                continue
                            elif merged_text and not merged_text.endswith(' '):
                                # Add without space for continuation
                                merged_text += text
                            else:
                                merged_text += text
                        else:
                            # Non-overlapping span - add with appropriate spacing
                            if merged_text and not merged_text.endswith(' '):
                                merged_text += " " + text
                            else:
                                merged_text += text
                        
                        last_end_x = block.bbox[2]
                    
                    if merged_text.strip():
                        title_lines.append(merged_text.strip())
                        title_blocks.extend(group)
                
                # Combine title lines
                if title_lines:
                    title = ' '.join(title_lines)
                    # Clean up common fragmentation artifacts
                    title = re.sub(r'\s+', ' ', title)  # Multiple spaces to single
                    title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)  # Add space before capitals
                    # Remove duplicate words that often appear in fragmented text
                    words = title.split()
                    cleaned_words = []
                    for i, word in enumerate(words):
                        # Skip if this word is very similar to the previous word
                        if i > 0 and (word == words[i-1] or 
                                    (len(word) > 3 and len(words[i-1]) > 3 and 
                                     word.lower() in words[i-1].lower())):
                            continue
                        cleaned_words.append(word)
                    
                    title = ' '.join(cleaned_words)
            else:
                # Single page logic (existing)
                if total_pages == 1:
                    title_candidates = [b for b in sorted_fp if b.font_size >= max_fs * 0.8]
                    for b in title_candidates[:3]:
                        if (b.is_centered or b.font_size >= max_fs * 0.9) and len(b.text.strip()) > 3:
                            title_blocks.append(b)
                            break
                else:
                    title_blocks = [b for b in sorted_fp if b.font_size >= max_fs * 0.9 and b.is_centered]
                
                if title_blocks:
                    title_blocks = sorted(title_blocks, key=lambda b: b.y_position)
                    if len(title_blocks) == 1:
                        title = title_blocks[0].text.strip()
                    else:
                        title = ' '.join(b.text.strip() for b in title_blocks).strip()
        
        # Track title texts to exclude from outline
        title_texts = {b.text for b in title_blocks}

        # Detect document type for single-page documents
        total_pages = len(set(b.page_num for b in self.text_blocks))
        has_numbered_content = any(b.numbering_pattern for b in self.text_blocks)
        
        # Distinguish between posters and other single-page documents
        if total_pages == 1:
            # Check for poster characteristics: lots of promotional text, party/event related
            poster_indicators = ['party', 'invited', 'rsvp', 'hope', 'see you', 'address:']
            text_content = ' '.join(b.text.lower() for b in self.text_blocks)
            has_poster_indicators = sum(1 for indicator in poster_indicators if indicator in text_content) >= 2
            
            # Check for form-like fields
            form_indicators = ['date:', 'time:', 'for:', 'address:', 'rsvp:']
            has_form_fields = sum(1 for indicator in form_indicators if indicator in text_content) >= 3
            
            is_poster = has_poster_indicators or has_form_fields
            
            if is_poster and not has_numbered_content:
                # Handle as poster (invitation, party flyer, etc.)
                poster_candidates = []
                for b in candidates:
                    # Skip common poster metadata words but keep single letters
                    if b.text.strip().upper() in ['ADDRESS:', 'RSVP:', 'DATE:', 'TIME:', 'FOR:']:
                        continue
                    # Skip URLs and contact info patterns
                    if re.search(r'www\.|\.com|@|\d{5}|\(\d{3}\)', b.text.lower()):
                        continue
                    # Skip very long fine print text
                    if b.char_count > 50 and b.font_size < self.baseline_font_size:
                        continue
                    poster_candidates.append(b)
                
                if poster_candidates:
                    # Group candidates by proximity to form phrases
                    phrase_groups = []
                    used_blocks = set()
                    
                    # Sort all candidates by position for better grouping
                    sorted_candidates = sorted(poster_candidates, key=lambda x: (x.y_position, x.x_position))
                    
                    for candidate in sorted_candidates:
                        if candidate in used_blocks:
                            continue
                            
                        # Find nearby blocks that could form a phrase
                        phrase_blocks = [candidate]
                        used_blocks.add(candidate)
                        
                        # Look for all blocks that are close to this one
                        for other in sorted_candidates:
                            if other in used_blocks:
                                continue
                            
                            # Check if blocks are on the same line (very close Y position)
                            y_diff = abs(other.y_position - candidate.y_position)
                            if y_diff <= max(candidate.font_size * 0.1, 2):  # Very tight Y tolerance
                                # Check horizontal proximity - should be reasonably close
                                x_gap = float('inf')
                                for block in phrase_blocks:
                                    x_gap = min(x_gap, 
                                              abs(other.x_position - block.bbox[2]),  # left to right edge
                                              abs(block.x_position - other.bbox[2]))  # right to left edge
                                
                                # Allow reasonable horizontal gaps for same-line text
                                if x_gap < max(candidate.font_size * 2, 20):
                                    phrase_blocks.append(other)
                                    used_blocks.add(other)
                        
                        if len(phrase_blocks) > 1:  # Only keep multi-block phrases
                            # Sort by X position for correct reading order
                            phrase_blocks.sort(key=lambda x: x.x_position)
                            phrase_groups.append(phrase_blocks)
                    
                    # Find the best phrase group (largest font, most words)
                    if phrase_groups:
                        best_group = max(phrase_groups, 
                                       key=lambda g: (max(b.font_size for b in g), 
                                                    sum(len(b.text.split()) for b in g)))
                        
                        # Combine the text from the best group
                        combined_text = ' '.join(b.text.strip() for b in best_group).strip()
                        
                        # Only include if it's substantial text
                        if len(combined_text) > 5 and not re.match(r'^[\d\s\-\(\)\.]+$', combined_text):
                            outline = [{'level': 'H1', 'text': combined_text + ' ', 'page': 0}]
                            return "", outline
                
                # If no good candidates found, return empty
                return "", []
            else:
                # Handle as regular single-page document (like STEM pathways)
                # For non-poster single-page docs, ensure we have a title and extract any headings
                if not title:
                    # If no title was detected, use the largest text as title
                    if first_page_blocks:
                        largest_block = max(first_page_blocks, key=lambda b: b.font_size)
                        title = largest_block.text.strip()
                        title_texts.add(largest_block.text)
                
                # Look for prominent headings that aren't the title
                outline = []
                heading_candidates = []
                for b in candidates:
                    if b.text in title_texts:
                        continue
                    # For single page docs, look for uppercase headings or large text
                    if (b.text_case == "UPPER" and len(b.text.strip()) > 5) or b.font_size >= self.baseline_font_size * 1.2:
                        heading_candidates.append(b)
                
                # Sort by font size and prominence, take only the most prominent
                if heading_candidates:
                    # Get the most prominent heading - prefer those higher up (smaller Y), then larger font
                    best_heading = min(heading_candidates, 
                                     key=lambda b: (b.y_position, -b.font_size))
                    text = best_heading.text.strip()
                    outline.append({'level': 'H1', 'text': text, 'page': 0})
                
                return title, outline
        
        # Enhanced heading level classification using font size tiers
        clusters = defaultdict(list)
        level_map = {}
        
        # First pass: assign levels based on font size tiers
        if hasattr(self, 'heading_size_tiers') and self.heading_size_tiers:
            for i, tier_size in enumerate(self.heading_size_tiers):
                level = f"H{i+1}"
                # Map both bold and non-bold variants of this size
                level_map[(tier_size, True)] = level
                level_map[(tier_size, False)] = level
        
        # Second pass: handle remaining sizes with traditional clustering
        for b in candidates:
            if not b.numbering_pattern:
                size_key = (round(b.font_size), b.is_bold)
                
                # Check if this size is already mapped via tiers
                exact_tier_match = False
                for tier_size in getattr(self, 'heading_size_tiers', []):
                    if abs(b.font_size - tier_size) < 0.5:
                        level_map[size_key] = level_map.get((tier_size, b.is_bold), f"H{len(self.heading_size_tiers)+1}")
                        exact_tier_match = True
                        break
                
                if not exact_tier_match:
                    clusters[size_key].append(b)
        
        # Assign levels to remaining clusters
        remaining_clusters = sorted(clusters.items(), key=lambda x: -x[0][0])  # Sort by font size desc
        level_counter = len(getattr(self, 'heading_size_tiers', [])) + 1
        
        for size_key, blocks in remaining_clusters:
            if size_key not in level_map:
                level_map[size_key] = f"H{min(level_counter, 6)}"
                level_counter += 1

        outline = []
        for b in candidates:
            # skip title blocks
            if b.text in title_texts:
                continue
            # skip title page blocks
            if b.page_num == 0:
                continue
            # only include non-numbered headings if not lowercase or if they're substantial
            if not b.numbering_pattern and (b.text_case == 'Lower' and len(b.text.strip()) < 10):
                continue
            
            # Assign level by numbering pattern first
            if b.numbering_pattern == 'x.':
                level = 'H1'
            elif b.numbering_pattern == 'x.y.':
                level = 'H2'
            elif b.numbering_pattern == 'x.y.z.':
                level = 'H3'
            else:
                # Use tier-based classification first
                level = None
                for i, tier_size in enumerate(getattr(self, 'heading_size_tiers', [])):
                    if abs(b.font_size - tier_size) < 0.5:
                        level = f"H{i+1}"
                        break
                
                # Fallback to font size key if not in tiers
                if not level:
                    font_key = (round(b.font_size), b.is_bold)
                    level = level_map.get(font_key, 'H4')  # Default fallback
            
            # Clean up text
            text = b.text.strip()
            
            # Add trailing space if missing (to match expected format)
            if not text.endswith(' '):
                text += ' '
            
            # Determine 0-based page (matching expected output format)
            page = b.page_num
            outline.append({'level': level, 'text': text, 'page': page})

        outline.sort(key=lambda x: (x['page'], next((b.y_position for b in self.text_blocks if b.text == x['text']), 0)))
        return title, outline