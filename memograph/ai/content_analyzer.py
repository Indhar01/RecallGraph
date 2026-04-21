"""Content analysis for automatic tagging and categorization."""

from typing import List, Dict, Any, Optional, Tuple
import re
from collections import Counter
import numpy as np


class ContentAnalyzer:
    """Analyze note content for automatic tagging and categorization."""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self._stop_words = self._load_stop_words()
        self._tag_patterns = self._compile_tag_patterns()
    
    def _load_stop_words(self) -> set:
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'when', 'where', 'why', 'how'
        }
    
    def _compile_tag_patterns(self) -> Dict[str, re.Pattern]:
        return {
            'hashtag': re.compile(r'#(\w+)'),
            'code_block': re.compile(r'```[\w]*\n(.*?)```', re.DOTALL),
            'inline_code': re.compile(r'`([^`]+)`'),
            'url': re.compile(r'https?://[^\s]+'),
            'wikilink': re.compile(r'\[\[([^\]]+)\]\]'),
        }
    
    def extract_keywords(self, content: str, max_keywords: int = 10, min_frequency: int = 2) -> List[Tuple[str, int]]:
        """Extract keywords from content using frequency analysis."""
        clean_content = self._clean_content(content)
        words = re.findall(r'\b[a-z]{3,}\b', clean_content.lower())
        words = [w for w in words if w not in self._stop_words]
        word_freq = Counter(words)
        return [(word, freq) for word, freq in word_freq.most_common(max_keywords) if freq >= min_frequency]
    
    def _clean_content(self, content: str) -> str:
        content = self._tag_patterns['code_block'].sub('', content)
        content = self._tag_patterns['inline_code'].sub('', content)
        content = self._tag_patterns['url'].sub('', content)
        return content
    
    def extract_existing_tags(self, content: str) -> List[str]:
        return self._tag_patterns['hashtag'].findall(content)
    
    def analyze_structure(self, content: str) -> Dict[str, Any]:
        return {
            'heading_count': len(re.findall(r'^#{1,6}\s', content, re.MULTILINE)),
            'list_count': len(re.findall(r'^\s*[-*+]\s', content, re.MULTILINE)),
            'code_block_count': len(self._tag_patterns['code_block'].findall(content)),
            'link_count': len(self._tag_patterns['wikilink'].findall(content)),
            'word_count': len(content.split()),
            'has_frontmatter': content.strip().startswith('---'),
        }
    
    def detect_content_type(self, content: str, title: str = "") -> str:
        structure = self.analyze_structure(content)
        if structure['code_block_count'] > 3:
            return 'code'
        if structure['word_count'] > 1000 and structure['heading_count'] > 3:
            return 'article'
        if structure['list_count'] > 10:
            return 'list'
        if structure['link_count'] > 5:
            return 'reference'
        return 'note'
    
    async def get_semantic_keywords(self, content: str, top_k: int = 10) -> List[Tuple[str, float]]:
        if not self.kernel.embedding_adapter:
            freq_keywords = self.extract_keywords(content, max_keywords=top_k)
            return [(kw, float(freq)) for kw, freq in freq_keywords]
        
        all_nodes = list(self.kernel.graph.all_nodes())
        all_tags = set()
        for node in all_nodes:
            if hasattr(node, 'tags'):
                all_tags.update(node.tags)
        
        if not all_tags:
            freq_keywords = self.extract_keywords(content, max_keywords=top_k)
            return [(kw, float(freq)) for kw, freq in freq_keywords]
        
        content_embedding = await self.kernel.embedding_adapter.embed_async(content)
        tag_scores = []
        for tag in all_tags:
            tag_embedding = await self.kernel.embedding_adapter.embed_async(tag)
            similarity = self._cosine_similarity(content_embedding, tag_embedding)
            tag_scores.append((tag, similarity))
        
        tag_scores.sort(key=lambda x: x[1], reverse=True)
        return tag_scores[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        vec1, vec2 = np.array(vec1), np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm1, norm2 = np.linalg.norm(vec1), np.linalg.norm(vec2)
        return float(dot_product / (norm1 * norm2)) if norm1 and norm2 else 0.0