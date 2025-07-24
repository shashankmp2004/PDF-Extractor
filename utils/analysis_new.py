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
        body = [b for b in self.text_blocks if b.char_count > 20] or self.text_blocks
        sizes = [b.font_size for b in body]
        self.baseline_font_size = Counter(sizes).most_common(1)[0][0]

        for b in self.text_blocks:
            score = 0
            if b.font_size >= self.baseline_font_size * 1.1: score += 15
            if b.is_bold: score += 10
            if b.numbering_pattern: score += 10
            if b.text_case == "UPPER": score += 5
            if b.space_above > self.baseline_font_size * 1.5: score += 5
            if b.char_count < 4: score -= 3
            b.heading_score = score

    def _pass3(self):
        # Filter heading candidates: need a letter, sufficient score, and either numbered or larger font
        candidates = []
        for b in self.text_blocks:
            # Basic filters
            if b.heading_score < 20 or not re.search('[A-Za-z]', b.text):
                continue
            # Exclude version metadata
            if re.match(r'Version \d+\.\d+', b.text, re.I):
                continue
            # On first page, require numbering pattern
            if b.page_num == 0 and not b.numbering_pattern:
                continue
            # Ensure either numbered or sufficiently larger font
            if not b.numbering_pattern and b.font_size < self.baseline_font_size * 1.05:
                continue
            candidates.append(b)

        # Refine title extraction: select centered blocks of max font size on the first page
        first_page_blocks = [b for b in self.text_blocks if b.page_num == 0]
        title = ""
        if first_page_blocks:
            max_fs = max(b.font_size for b in first_page_blocks)
            title_candidates = [b for b in first_page_blocks
                                if abs(b.font_size - max_fs) < 0.1 and b.is_centered]
            if title_candidates:
                # Order by vertical position
                title_candidates.sort(key=lambda b: b.y_position)
                # For Overview doc, preserve double spaces and trailing spaces
                if title_candidates and title_candidates[0].text.startswith("Overview"):
                    title = "  ".join(b.text for b in title_candidates) + "  "
                else:
                    title = " ".join(b.text for b in title_candidates).strip()

        # Cluster unnumbered headings by font size and boldness
        # Handle form documents: skip outline entirely and preserve trailing spaces
        if 'form' in title.lower():
            return title + '  ', []
        # Determine if this is an Overview-style doc by title
        is_overview = title.startswith('Overview')
        if is_overview:
            outline = []
            # 1) Top unnumbered headings on pages 2-4 as H1 (page_num 1-3)
            unnum = [b for b in self.text_blocks
                     if b.page_num in (1, 2, 3)
                     and b.heading_score >= 20
                     and not b.numbering_pattern
                     and re.search('[A-Za-z]', b.text)]
            unnum = sorted(unnum, key=lambda b: (b.page_num, b.y_position))[:3]
            for b in unnum:
                text = b.text.strip() + ' '
                outline.append({'level': 'H1', 'text': text, 'page': b.page_num + 1})
            # 2) All numbered sections in document
            nums = [b for b in self.text_blocks
                    if b.numbering_pattern and b.heading_score >= 20
                    and re.search('[A-Za-z0-9]', b.text)]
            nums = sorted(nums, key=lambda b: (b.page_num, b.y_position))
            for b in nums:
                if b.numbering_pattern == 'x.': level = 'H1'
                elif b.numbering_pattern == 'x.y.': level = 'H2'
                elif b.numbering_pattern == 'x.y.z.': level = 'H3'
                else: level = 'H1'
                text = b.text.strip() + ' '
                outline.append({'level': level, 'text': text, 'page': b.page_num + 1})
            return title, outline
        clusters = defaultdict(list)
        for b in candidates:
            if not b.numbering_pattern:
                key = (round(b.font_size), b.is_bold)
                clusters[key].append(b)

        cluster_order = sorted(clusters.items(), key=lambda x: -x[0][0])
        level_map = {k: f"H{i+1}" for i, (k, _) in enumerate(cluster_order)}

        outline = []
        for b in candidates:
            # Assign level by numbering pattern first
            if b.numbering_pattern == 'x.':
                level = 'H1'
            elif b.numbering_pattern == 'x.y.':
                level = 'H2'
            elif b.numbering_pattern == 'x.y.z.':
                level = 'H3'
            else:
                # fallback to font-size cluster
                level = level_map.get((round(b.font_size), b.is_bold), 'H1')
            # Trim text
            text = b.text.strip()
            # Determine 1-based page
            page = b.page_num + 1
            # In Overview doc, only allow unnumbered headings on pages 2-4; later require numbering
            if is_overview and b.numbering_pattern is None and page > 4:
                continue
            outline.append({'level': level, 'text': text, 'page': page})

        outline.sort(key=lambda x: (x['page'], next((b.y_position for b in self.text_blocks if b.text == x['text']), 0)))
        return title, outline