import re
import unicodedata
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict

class PatternLearner:
    def __init__(self):
        self.learned_patterns = {}
    
    def detect_numbering_patterns(self, text_blocks: List['TextBlock']) -> List[Tuple[str, str]]:
        """Dynamically detect numbering patterns from the document (OCR-enhanced)"""
        patterns = []
        
        # Analyze all text blocks to find common numbering patterns
        numbering_candidates = []
        for block in text_blocks:
            head = block.text[:15].strip()  # Slightly longer for OCR text
            if head and len(head) < 10:  # Short text likely to be numbering
                # Clean OCR artifacts
                head = self._clean_ocr_text(head)
                if head:
                    numbering_candidates.append(head)
        
        # Enhanced pattern detection with OCR noise tolerance
        test_patterns = [
            # Digit-based patterns (most common)
            (r'^\d+\.', 'x.'),
            (r'^\d+\)', 'x)'),
            (r'^\d+[-－—]', 'x-'),
            
            # Letter-based patterns  
            (r'^[A-Za-z]\.', 'A.'),
            (r'^[A-Za-z]\)', 'A)'),
            
            # Roman numeral patterns
            (r'^[IVXLCDMivxlcdm]+\.', 'I.'),
            
            # CJK patterns (Unicode ranges)
            (r'^[第章節条項目部編巻冊]\d*[章節条項目]', 'x.'),
            (r'^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓]', 'x.'),
            
            # Arabic/Persian numerals
            (r'^[٠-٩]+\.', 'x.'),
            (r'^[۰-۹]+\.', 'x.'),
            
            # OCR-specific: sometimes numbers get recognized as letters
            (r'^[Oo0]\d*\.', 'x.'),  # O/0 confusion
            (r'^[Il1]\d*\.', 'x.'),  # I/l/1 confusion
        ]
        
        # Only include patterns actually found in document
        for pattern, tag in test_patterns:
            if any(re.match(pattern, candidate, re.UNICODE) for candidate in numbering_candidates):
                patterns.append((pattern, tag))
        
        # Add hierarchical patterns if simple ones are found
        if any(tag == 'x.' for _, tag in patterns):
            # Check for actual hierarchical patterns in text
            hierarchical_candidates = [c for c in numbering_candidates if len(c.split('.')) > 2]
            if hierarchical_candidates:
                patterns.extend([
                    (r'^\d+\.\d+\.', 'x.y.'),
                    (r'^\d+\.\d+\.\d+\.', 'x.y.z.'),
                ])
        
        return patterns
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean common OCR artifacts"""
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fix common OCR substitutions
        ocr_fixes = {
            'O': '0',  # Letter O -> Zero
            'l': '1',  # Lowercase L -> One  
            'I': '1',  # Uppercase I -> One
            'S': '5',  # Sometimes S -> 5
            'G': '6',  # Sometimes G -> 6
        }
        
        # Only apply fixes if it looks like a numbering pattern
        if re.match(r'^[A-Za-z0-9]+[.\)-]', text):
            for old, new in ocr_fixes.items():
                if text.startswith(old) and len(text) > 1 and text[1] in '0123456789.)-':
                    text = new + text[1:]
                    break
        
        return text
    
    def detect_font_indicators(self, text_blocks: List['TextBlock']) -> List[str]:
        """Learn bold indicators from actual font names (OCR-enhanced)"""
        font_names = [block.font_name.lower() for block in text_blocks if block.font_name != "OCR-Font"]
        bold_indicators = set()
        
        # Extract bold keywords from actual fonts (skip OCR-Font)
        for font_name in font_names:
            words = re.split(r'[-_\s]', font_name)
            for word in words:
                if word.lower() in ['bold', 'black', 'heavy', 'demi', 'semi', 'medium', 'thick']:
                    bold_indicators.add(word.lower())
                # International bold indicators
                if word.lower() in ['gras', 'fett', 'grassetto', 'negrito', 'negrita']:
                    bold_indicators.add(word.lower())
        
        # For OCR text, we'll need to use size-based detection
        if not bold_indicators:
            bold_indicators = {'bold', 'black', 'heavy'}
            
        return list(bold_indicators)
    
    def detect_content_indicators(self, text_blocks: List['TextBlock']) -> Dict[str, List[str]]:
        """Detect document type indicators from actual content (OCR-tolerant)"""
        all_text = ' '.join(block.text.lower() for block in text_blocks)
        
        # Clean OCR noise for better detection
        all_text = re.sub(r'\s+', ' ', all_text)
        
        indicators = {
            'academic': [],
            'form': [],
            'social': []
        }
        
        # Academic indicators with OCR tolerance
        academic_terms = []
        academic_keywords = [
            'abstract', 'introduction', 'conclusion', 'references', 'bibliography',
            'conference', 'symposium', 'workshop', 'proceedings', 'paper',
            'research', 'study', 'analysis', 'method', 'results'
        ]
        
        for keyword in academic_keywords:
            # Allow for OCR errors (1-2 character differences)
            pattern = self._create_fuzzy_pattern(keyword)
            if re.search(pattern, all_text, re.IGNORECASE):
                academic_terms.append(keyword)
        
        # Form indicators with OCR tolerance
        form_terms = []
        form_patterns = [
            r'\b(name|email|phone|address|date|time)\s*[:：]',
            r'\b(nom|courriel|téléphone|adresse|date|heure)\s*[:：]',
            r'\b(nombre|correo|teléfono|dirección|fecha|hora)\s*[:：]',
            r'\b(姓名|邮箱|电话|地址|日期|时间)\s*[:：]',
        ]
        
        for pattern in form_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            form_terms.extend(matches)
        
        # Social indicators  
        social_terms = []
        social_keywords = ['invitation', 'party', 'rsvp', 'event', 'celebration', 'wedding']
        
        for keyword in social_keywords:
            pattern = self._create_fuzzy_pattern(keyword)
            if re.search(pattern, all_text, re.IGNORECASE):
                social_terms.append(keyword)
        
        indicators['academic'] = list(set(academic_terms))
        indicators['form'] = list(set(form_terms))
        indicators['social'] = list(set(social_terms))
        
        return indicators
    
    def _create_fuzzy_pattern(self, word: str) -> str:
        """Create regex pattern that allows for 1-2 OCR errors"""
        if len(word) <= 4:
            return re.escape(word)  # Short words - exact match
        
        # Allow 1 character substitution/insertion/deletion for longer words
        chars = list(word)
        patterns = [re.escape(word)]  # Exact match
        
        # Allow common OCR substitutions
        ocr_subs = {'o': '[o0]', 'i': '[il1]', 'l': '[il1]', 's': '[s5]', 'g': '[g6]'}
        
        fuzzy_word = word
        for char, replacement in ocr_subs.items():
            if char in fuzzy_word:
                fuzzy_word = fuzzy_word.replace(char, replacement)
        
        patterns.append(fuzzy_word)
        
        return '|'.join(patterns)

# Global pattern learner
_pattern_learner = PatternLearner()

class TextBlock:
    def __init__(self, text: str, font_size: float, font_name: str, 
                 bbox: Tuple[float, float, float, float], page_num: int, is_italic: bool = False):
        # Clean text for OCR artifacts
        self.text = self._clean_text(text.strip())
        self.font_size = font_size
        self.font_name = font_name
        self.bbox = bbox
        self.page_num = page_num
        self.is_italic = is_italic
        self.is_ocr_text = font_name == "OCR-Font"

        self.x_position = bbox[0]
        self.y_position = bbox[1]
        self.is_bold = self._detect_bold()
        self.text_case = self._categorize_text_case()
        self.char_count = len(self.text)
        self.numbering_pattern = None  # Will be set by DocumentAnalyzer

        self.space_above = 0.0
        self.is_isolated = False
        self.is_centered = False
        self.heading_score = 0.0

    def _clean_text(self, text: str) -> str:
        """Clean OCR artifacts and normalize text"""
        if not text:
            return text
            
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR character confusions in specific contexts
        # Only apply fixes that are contextually safe
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])\s*([A-Za-z\u4e00-\u9fff])', r'\1 \2', text)
        
        return text.strip()

    def _detect_bold(self) -> bool:
        """Enhanced bold detection for OCR text"""
        if self.is_ocr_text:
            # For OCR text, bold detection is harder - use size as proxy
            # This will be enhanced by DocumentAnalyzer with learned patterns
            return False  # Default to false, will be updated by analyzer
        else:
            # Standard font-based detection
            basic_keywords = ['bold', 'black', 'heavy', 'demi', 'semi'] 
            font_lower = self.font_name.lower()
            return any(keyword in font_lower for keyword in basic_keywords)

    def _categorize_text_case(self) -> str:
        """Enhanced case detection with OCR tolerance"""
        if not self.text:
            return "Lower"
        
        # For CJK text, case concepts don't apply the same way
        if any('\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u309f' or 
               '\u30a0' <= c <= '\u30ff' or '\uac00' <= c <= '\ud7af' for c in self.text):
            # CJK title detection
            if len(self.text.strip()) <= 8 and not any(c.isdigit() for c in self.text):
                return "Title Case"
            return "Lower"
        
        # Remove non-letter characters for case analysis
        letters_only = ''.join(c for c in self.text if unicodedata.category(c).startswith('L'))
        if not letters_only:
            return "Lower"
        
        # Enhanced case analysis with OCR tolerance
        upper_count = sum(1 for c in letters_only if c.isupper())
        lower_count = sum(1 for c in letters_only if c.islower())
        total_letters = len(letters_only)
        
        if total_letters == 0:
            return "Lower"
            
        upper_ratio = upper_count / total_letters
        
        # More tolerant thresholds for OCR text
        if self.is_ocr_text:
            if upper_ratio >= 0.8:  # 80% uppercase
                return "UPPER"
            elif upper_ratio >= 0.3 and self.text[0].isupper():  # First letter upper + significant caps
                return "Title Case"
        else:
            if upper_count == total_letters:
                return "UPPER"
            elif upper_count > 0 and self.text[0].isupper():
                # Check if it's title case pattern
                words = self.text.split()
                is_title = all(word[0].isupper() if word and unicodedata.category(word[0]).startswith('L') else True for word in words)
                if is_title:
                    return "Title Case"
        
        return "Lower"

    def detect_numbering_pattern(self, learned_patterns: List[Tuple[str, str]]) -> Optional[str]:
        """Detect numbering pattern using learned patterns (OCR-enhanced)"""
        head = self.text[:25].strip()  # Longer for OCR text
        
        # Clean the text for pattern matching
        if self.is_ocr_text:
            head = self._clean_ocr_numbering(head)
        
        for pattern, tag in learned_patterns:
            if re.match(pattern, head, re.UNICODE):
                return tag
        
        return None
    
    def _clean_ocr_numbering(self, text: str) -> str:
        """Clean OCR artifacts specifically for numbering pattern detection"""
        # Common OCR fixes for numbering
        fixes = [
            (r'^[Oo](\d)', r'0\1'),  # O -> 0 at start
            (r'^[Il](\d)', r'1\1'),  # I/l -> 1 at start  
            (r'^(\d+)[IlL]\.', r'\1.'),  # trailing I/l/L before dot -> nothing
            (r'^(\d+)\s*[.。]', r'\1.'),  # fix spacing before dot
        ]
        
        for pattern, replacement in fixes:
            text = re.sub(pattern, replacement, text)
            
        return text


class DocumentAnalyzer:
    def __init__(self):
        self.text_blocks: List[TextBlock] = []
        self.page_width = 0.0
        self.baseline_font_size = 0.0
        self.learned_patterns = []
        self.learned_bold_keywords = []
        self.document_indicators = {}

    def set_page_width(self, width: float):
        self.page_width = width

    def add_text_block(self, block: TextBlock):
        self.text_blocks.append(block)

    def analyze_document(self):
        # Learn patterns from the document first
        self._learn_document_patterns()
        self._pass1()
        self._pass2()
        return self._pass3()

    def _learn_document_patterns(self):
        """Learn patterns dynamically from the document content (OCR-enhanced)"""
        # Learn numbering patterns
        self.learned_patterns = _pattern_learner.detect_numbering_patterns(self.text_blocks)
        
        # Learn bold font indicators
        self.learned_bold_keywords = _pattern_learner.detect_font_indicators(self.text_blocks)
        
        # Learn content indicators
        self.document_indicators = _pattern_learner.detect_content_indicators(self.text_blocks)
        
        # Update all text blocks with learned patterns
        for block in self.text_blocks:
            block.numbering_pattern = block.detect_numbering_pattern(self.learned_patterns)
            
            # Enhanced bold detection for OCR text
            if block.is_ocr_text:
                # For OCR text, use size-based bold detection
                sizes = [b.font_size for b in self.text_blocks if not b.is_ocr_text]
                if sizes:
                    avg_size = sum(sizes) / len(sizes)
                    block.is_bold = block.font_size > avg_size * 1.2
                else:
                    # Fallback: larger OCR text is likely bold
                    all_sizes = [b.font_size for b in self.text_blocks]
                    if all_sizes:
                        avg_all_size = sum(all_sizes) / len(all_sizes)
                        block.is_bold = block.font_size > avg_all_size * 1.15
            else:
                # Standard font-based detection with learned keywords
                if self.learned_bold_keywords:
                    font_lower = block.font_name.lower()
                    block.is_bold = any(keyword in font_lower for keyword in self.learned_bold_keywords)

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
            
            # Enhanced bold scoring for OCR text
            if b.is_bold:
                if b.is_ocr_text:
                    # OCR bold detection is size-based, so give extra credit
                    if size_ratio >= 1.5: score += 15
                    elif size_ratio >= 1.3: score += 12
                    else: score += 8
                else:
                    # Font-based bold detection
                    if size_ratio >= 1.3: score += 12
                    else: score += 8
            
            if b.numbering_pattern:
                score += 18
            
            if b.text_case == "UPPER": score += 6
            elif b.text_case == "Title Case": score += 4
            
            if b.space_above > self.baseline_font_size * 1.5: score += 10
            
            if b.is_centered and size_ratio >= 1.2: score += 8
            
            # Enhanced character count scoring with OCR considerations
            char_count = b.char_count
            has_cjk = any(c for c in b.text if '\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
            
            if has_cjk:
                # CJK characters are more information-dense
                if char_count < 2: score -= 12
                elif 2 <= char_count <= 8: score += 3  # Slightly longer for OCR
                elif 9 <= char_count <= 25: score += 1
                elif char_count > 35: score -= 3
            else:
                # Regular scoring with OCR tolerance
                if b.is_ocr_text:
                    # OCR text may have different length characteristics
                    if char_count < 3: score -= 10
                    elif 3 <= char_count <= 60: score += 2  # More tolerant range
                    elif char_count > 120: score -= 5
                else:
                    # Standard scoring for clean text
                    if char_count < 4: score -= 8
                    elif 4 <= char_count <= 50: score += 2
                    elif char_count > 100: score -= 5
            
            # Penalty for very small font size
            if b.font_size < self.baseline_font_size * 0.95: score -= 8
            
            # OCR confidence bonus (if we had OCR confidence scores)
            if b.is_ocr_text:
                # OCR text tends to be noisier, so slightly reduce scores
                score = int(score * 0.95)
            
            b.heading_score = score

    def _pass3(self):
        total_pages = len(set(b.page_num for b in self.text_blocks))
        is_poster = total_pages == 1
        
        candidates = []
        for b in self.text_blocks:
            # Check if text contains meaningful content (multilingual)
            has_meaningful_content = bool(re.search(r'[A-Za-z\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff]', b.text))
            
            if is_poster:
                if b.heading_score < 20 or not has_meaningful_content:
                    continue
            else:
                if b.heading_score < 20 or not has_meaningful_content:
                    continue
                    
            # Skip version numbers
            if re.match(r'Version \d+\.\d+', b.text, re.I):
                continue
                
            # Additional filtering for short text (Japanese/CJK handling)
            if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in b.text):  # Japanese hiragana/katakana
                if len(b.text.strip()) <= 3 and not b.numbering_pattern and b.font_size < self.baseline_font_size * 1.4:
                    continue
                    
            if is_poster:
                if b.font_size < self.baseline_font_size * 1.3 and b.heading_score < 30:
                    continue
                if b.char_count < 8 and not (b.font_size > self.baseline_font_size * 1.5) and b.char_count > 1:
                    continue
            else:
                # For non-poster documents, be more strict about small text blocks
                if not b.numbering_pattern and b.font_size < self.baseline_font_size * 1.05:
                    continue
                # Skip very short text blocks unless they have strong indicators
                if b.char_count <= 4 and not b.numbering_pattern and b.heading_score < 35:
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
                    # Enhanced word boundary detection for multilingual text
                    title = re.sub(r'([a-z\u4e00-\u9fff\u0600-\u06ff\u0400-\u04ff])([A-Z\u4e00-\u9fff\u0600-\u06ff\u0400-\u04ff])', r'\1 \2', title)
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
            # Use learned document indicators instead of hardcoded ones
            all_text = ' '.join(b.text.lower() for b in self.text_blocks)
            
            # Check for academic indicators
            academic_indicators = self.document_indicators.get('academic', [])
            social_indicators = self.document_indicators.get('social', [])
            form_indicators = self.document_indicators.get('form', [])
            
            has_academic_indicators = len(academic_indicators) > 0
            has_social_indicators = len(social_indicators) > 0
            has_form_indicators = len(form_indicators) >= 2
            
            is_poster = has_academic_indicators or has_social_indicators or has_form_indicators
            
            if is_poster and not has_numbered_content:
                poster_candidates = []
                for b in candidates:
                    # Skip form field-like labels dynamically
                    text_upper = b.text.strip().upper()
                    is_field_label = any(label.upper() + ':' == text_upper for label in form_indicators)
                    
                    if is_field_label:
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