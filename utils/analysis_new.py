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
        body = [b for b in self.text_blocks if b.char_count > 10 and b.font_size >= 8] or self.text_blocks
        sizes = [b.font_size for b in body]
        self.baseline_font_size = Counter(sizes).most_common(1)[0][0]
        
        size_counter = Counter(sizes)
        sorted_sizes = sorted(size_counter.keys(), reverse=True)
        
        size_tiers = []
        for i, size in enumerate(sorted_sizes):
            if size >= self.baseline_font_size * 1.15:
                blocks_with_size = [b for b in body if b.font_size == size]
                content_page_blocks = [b for b in blocks_with_size if b.page_num > 0]
                
                if (size_counter[size] >= 2 or size >= self.baseline_font_size * 1.5) and len(content_page_blocks) > 0:
                    size_tiers.append(size)
        
        if len(size_tiers) >= 2 and size_tiers[0] > size_tiers[1] * 1.3:
            self.heading_size_tiers = size_tiers[1:5]
        else:
            self.heading_size_tiers = size_tiers[:4]
        
        for b in self.text_blocks:
            score = 0
            
            size_ratio = b.font_size / self.baseline_font_size
            if b.font_size in self.heading_size_tiers:
                tier_index = self.heading_size_tiers.index(b.font_size)
                score += 25 - (tier_index * 3)
            elif size_ratio >= 2.0: score += 20
            elif size_ratio >= 1.5: score += 15
            elif size_ratio >= 1.2: score += 10
            elif size_ratio >= 1.1: score += 5
            
            if b.is_bold:
                if size_ratio >= 1.3: score += 12
                else: score += 8
            
            if b.numbering_pattern:
                score += 18
            
            if b.text_case == "UPPER": score += 6
            elif b.text_case == "Title Case": score += 4
            
            if b.space_above > self.baseline_font_size * 1.5: score += 10
            
            if b.is_centered and size_ratio >= 1.2: score += 8
            
            if b.char_count < 4: score -= 8
            elif 4 <= b.char_count <= 50: score += 2
            elif b.char_count > 100: score -= 5
            
            if b.font_size < self.baseline_font_size * 0.95: score -= 8
            
            b.heading_score = score

    def _pass3(self):
        total_pages = len(set(b.page_num for b in self.text_blocks))
        is_poster = total_pages == 1
        
        candidates = []
        for b in self.text_blocks:
            if is_poster:
                if b.heading_score < 20 or not re.search('[A-Za-z!]', b.text):
                    continue
            else:
                if b.heading_score < 20 or not re.search('[A-Za-z]', b.text):
                    continue
            if re.match(r'Version \d+\.\d+', b.text, re.I):
                continue
            if is_poster:
                if b.font_size < self.baseline_font_size * 1.3 and b.heading_score < 30:
                    continue
                if b.char_count < 8 and not (b.font_size > self.baseline_font_size * 1.5) and b.char_count > 1:
                    continue
            else:
                if not b.numbering_pattern and b.font_size < self.baseline_font_size * 1.05:
                    continue
            candidates.append(b)

        first_page_blocks = [b for b in self.text_blocks if b.page_num == 0]
        title = ""
        title_blocks = []
        
        if first_page_blocks:
            sorted_fp = sorted(first_page_blocks, key=lambda b: (-b.font_size, b.y_position))
            
            if not sorted_fp:
                return title, []
                
            max_fs = sorted_fp[0].font_size
            total_pages = len(set(b.page_num for b in self.text_blocks))
            
            if total_pages > 1:
                large_font_threshold = max_fs * 0.85
                title_candidates = [b for b in sorted_fp if b.font_size >= large_font_threshold]
                
                y_groups = {}
                for candidate in title_candidates:
                    found_group = False
                    for existing_y in y_groups.keys():
                        if abs(candidate.y_position - existing_y) <= max(candidate.font_size * 0.15, 3):
                            y_groups[existing_y].append(candidate)
                            found_group = True
                            break
                    
                    if not found_group:
                        y_groups[candidate.y_position] = [candidate]
                
                title_lines = []
                for y_pos, group in sorted(y_groups.items()):
                    group.sort(key=lambda x: x.x_position)
                    
                    merged_text = ""
                    last_end_x = -1000
                    
                    for block in group:
                        text = block.text.strip()
                        start_x = block.x_position
                        
                        if start_x < last_end_x + block.font_size * 0.2:
                            if text in merged_text or merged_text.endswith(text[:3]):
                                continue
                            elif merged_text and not merged_text.endswith(' '):
                                merged_text += text
                            else:
                                merged_text += text
                        else:
                            if merged_text and not merged_text.endswith(' '):
                                merged_text += " " + text
                            else:
                                merged_text += text
                        
                        last_end_x = block.bbox[2]
                    
                    if merged_text.strip():
                        title_lines.append(merged_text.strip())
                        title_blocks.extend(group)
                
                if title_lines:
                    title = ' '.join(title_lines)
                    title = re.sub(r'\s+', ' ', title)
                    title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)
                    words = title.split()
                    cleaned_words = []
                    for i, word in enumerate(words):
                        if i > 0 and (word == words[i-1] or 
                                    (len(word) > 3 and len(words[i-1]) > 3 and 
                                     word.lower() in words[i-1].lower())):
                            continue
                        cleaned_words.append(word)
                    
                    title = ' '.join(cleaned_words)
            else:
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
        
        title_texts = {b.text for b in title_blocks}

        total_pages = len(set(b.page_num for b in self.text_blocks))
        has_numbered_content = any(b.numbering_pattern for b in self.text_blocks)
        
        if total_pages == 1:
            poster_indicators = ['party', 'invited', 'rsvp', 'hope', 'see you', 'address:']
            text_content = ' '.join(b.text.lower() for b in self.text_blocks)
            has_poster_indicators = sum(1 for indicator in poster_indicators if indicator in text_content) >= 2
            
            form_indicators = ['date:', 'time:', 'for:', 'address:', 'rsvp:']
            has_form_fields = sum(1 for indicator in form_indicators if indicator in text_content) >= 3
            
            is_poster = has_poster_indicators or has_form_fields
            
            if is_poster and not has_numbered_content:
                poster_candidates = []
                for b in candidates:
                    if b.text.strip().upper() in ['ADDRESS:', 'RSVP:', 'DATE:', 'TIME:', 'FOR:']:
                        continue
                    if re.search(r'www\.|\.com|@|\d{5}|\(\d{3}\)', b.text.lower()):
                        continue
                    if b.char_count > 50 and b.font_size < self.baseline_font_size:
                        continue
                    poster_candidates.append(b)
                
                if poster_candidates:
                    phrase_groups = []
                    used_blocks = set()
                    
                    sorted_candidates = sorted(poster_candidates, key=lambda x: (x.y_position, x.x_position))
                    
                    for candidate in sorted_candidates:
                        if candidate in used_blocks:
                            continue
                            
                        phrase_blocks = [candidate]
                        used_blocks.add(candidate)
                        
                        for other in sorted_candidates:
                            if other in used_blocks:
                                continue
                            
                            y_diff = abs(other.y_position - candidate.y_position)
                            if y_diff <= max(candidate.font_size * 0.1, 2):
                                x_gap = float('inf')
                                for block in phrase_blocks:
                                    x_gap = min(x_gap, 
                                              abs(other.x_position - block.bbox[2]),
                                              abs(block.x_position - other.bbox[2]))
                                
                                if x_gap < max(candidate.font_size * 2, 20):
                                    phrase_blocks.append(other)
                                    used_blocks.add(other)
                        
                        if len(phrase_blocks) > 1:
                            phrase_blocks.sort(key=lambda x: x.x_position)
                            phrase_groups.append(phrase_blocks)
                    
                    if phrase_groups:
                        best_group = max(phrase_groups, 
                                       key=lambda g: (max(b.font_size for b in g), 
                                                    sum(len(b.text.split()) for b in g)))
                        
                        combined_text = ' '.join(b.text.strip() for b in best_group).strip()
                        
                        if len(combined_text) > 5 and not re.match(r'^[\d\s\-\(\)\.]+$', combined_text):
                            outline = [{'level': 'H1', 'text': combined_text + ' ', 'page': 0}]
                            return "", outline
                
                return "", []
            else:
                if not title:
                    if first_page_blocks:
                        largest_block = max(first_page_blocks, key=lambda b: b.font_size)
                        title = largest_block.text.strip()
                        title_texts.add(largest_block.text)
                
                outline = []
                heading_candidates = []
                for b in candidates:
                    if b.text in title_texts:
                        continue
                    if (b.text_case == "UPPER" and len(b.text.strip()) > 5) or b.font_size >= self.baseline_font_size * 1.2:
                        heading_candidates.append(b)
                
                if heading_candidates:
                    best_heading = min(heading_candidates, 
                                     key=lambda b: (b.y_position, -b.font_size))
                    text = best_heading.text.strip()
                    outline.append({'level': 'H1', 'text': text, 'page': 0})
                
                return title, outline
        
        clusters = defaultdict(list)
        level_map = {}
        
        if hasattr(self, 'heading_size_tiers') and self.heading_size_tiers:
            for i, tier_size in enumerate(self.heading_size_tiers):
                level = f"H{i+1}"
                level_map[(tier_size, True)] = level
                level_map[(tier_size, False)] = level
        
        for b in candidates:
            if not b.numbering_pattern:
                size_key = (round(b.font_size), b.is_bold)
                
                exact_tier_match = False
                for tier_size in getattr(self, 'heading_size_tiers', []):
                    if abs(b.font_size - tier_size) < 0.5:
                        level_map[size_key] = level_map.get((tier_size, b.is_bold), f"H{len(self.heading_size_tiers)+1}")
                        exact_tier_match = True
                        break
                
                if not exact_tier_match:
                    clusters[size_key].append(b)
        
        remaining_clusters = sorted(clusters.items(), key=lambda x: -x[0][0])
        level_counter = len(getattr(self, 'heading_size_tiers', [])) + 1
        
        for size_key, blocks in remaining_clusters:
            if size_key not in level_map:
                level_map[size_key] = f"H{min(level_counter, 6)}"
                level_counter += 1

        outline = []
        for b in candidates:
            if b.text in title_texts:
                continue
            if b.page_num == 0:
                continue
            if not b.numbering_pattern and (b.text_case == 'Lower' and len(b.text.strip()) < 10):
                continue
            
            if b.numbering_pattern == 'x.':
                level = 'H1'
            elif b.numbering_pattern == 'x.y.':
                level = 'H2'
            elif b.numbering_pattern == 'x.y.z.':
                level = 'H3'
            else:
                level = None
                for i, tier_size in enumerate(getattr(self, 'heading_size_tiers', [])):
                    if abs(b.font_size - tier_size) < 0.5:
                        level = f"H{i+1}"
                        break
                
                if not level:
                    font_key = (round(b.font_size), b.is_bold)
                    level = level_map.get(font_key, 'H4')
            
            text = b.text.strip()
            
            if not text.endswith(' '):
                text += ' '
            
            page = b.page_num
            outline.append({'level': level, 'text': text, 'page': page})

        outline.sort(key=lambda x: (x['page'], next((b.y_position for b in self.text_blocks if b.text == x['text']), 0)))
        return title, outline