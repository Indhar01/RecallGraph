"""Automatic tag suggestion for notes."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from memograph.ai.content_analyzer import ContentAnalyzer


@dataclass
class TagSuggestion:
    tag: str
    confidence: float
    reason: str
    source: str


class AutoTagger:
    def __init__(self, kernel, min_confidence: float = 0.3, max_suggestions: int = 5):
        self.kernel = kernel
        self.analyzer = ContentAnalyzer(kernel)
        self.min_confidence = min_confidence
        self.max_suggestions = max_suggestions
        self._tag_history: Dict[str, int] = {}

    async def suggest_tags(
        self, content: str, title: str = "", existing_tags: Optional[List[str]] = None
    ) -> List[TagSuggestion]:
        existing_tags = existing_tags or []
        suggestions = []

        suggestions.extend(self._suggest_from_frequency(content))
        suggestions.extend(await self._suggest_from_semantics(content))
        suggestions.extend(self._suggest_from_structure(content, title))
        suggestions.extend(await self._suggest_from_related_notes(content))

        suggestions = [
            s
            for s in suggestions
            if s.tag not in existing_tags and s.confidence >= self.min_confidence
        ]
        suggestions = self._merge_suggestions(suggestions)
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[: self.max_suggestions]

    def _suggest_from_frequency(self, content: str) -> List[TagSuggestion]:
        keywords = self.analyzer.extract_keywords(content, max_keywords=10)
        return [
            TagSuggestion(
                kw, min(freq / 10.0, 1.0) * 0.6, f"Appears {freq}x", "frequency"
            )
            for kw, freq in keywords
        ]

    async def _suggest_from_semantics(self, content: str) -> List[TagSuggestion]:
        keywords = await self.analyzer.get_semantic_keywords(content, top_k=10)
        return [
            TagSuggestion(kw, sim * 0.9, f"Similar: {sim:.2f}", "semantic")
            for kw, sim in keywords
        ]

    def _suggest_from_structure(self, content: str, title: str) -> List[TagSuggestion]:
        content_type = self.analyzer.detect_content_type(content, title)
        structure = self.analyzer.analyze_structure(content)
        suggestions = [
            TagSuggestion(content_type, 0.8, f"Type: {content_type}", "structure")
        ]
        if structure["code_block_count"] > 0:
            suggestions.append(
                TagSuggestion(
                    "code", 0.7, f"{structure['code_block_count']} blocks", "structure"
                )
            )
        return suggestions

    async def _suggest_from_related_notes(self, content: str) -> List[TagSuggestion]:
        try:
            similar = await self.kernel.retrieve_nodes_async(
                query=content[:500], top_k=5
            )
            tag_counts = {}
            for node in similar:
                if hasattr(node, "tags"):
                    for tag in node.tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            total = len(similar)
            return [
                TagSuggestion(
                    tag, (cnt / total) * 0.7, f"{cnt}/{total} similar", "existing"
                )
                for tag, cnt in tag_counts.items()
            ]
        except:
            return []

    def _merge_suggestions(
        self, suggestions: List[TagSuggestion]
    ) -> List[TagSuggestion]:
        tag_map = {}
        for s in suggestions:
            tag_map.setdefault(s.tag, []).append(s)

        merged = []
        for tag, slist in tag_map.items():
            avg_conf = sum(s.confidence for s in slist) / len(slist)
            if len(slist) > 1:
                avg_conf = min(avg_conf * 1.2, 1.0)
            best = max(slist, key=lambda s: s.confidence)
            merged.append(
                TagSuggestion(
                    tag, avg_conf, best.reason, ",".join(set(s.source for s in slist))
                )
            )
        return merged

    def record_feedback(self, tag: str, accepted: bool):
        self._tag_history[tag] = self._tag_history.get(tag, 0) + (1 if accepted else -1)

    def get_tag_stats(self) -> Dict[str, Any]:
        if not self._tag_history:
            return {
                "total_suggestions": 0,
                "accepted_tags": [],
                "rejected_tags": [],
                "acceptance_rate": 0.0,
            }
        accepted = {t: c for t, c in self._tag_history.items() if c > 0}
        rejected = {t: abs(c) for t, c in self._tag_history.items() if c < 0}
        total = sum(abs(c) for c in self._tag_history.values())
        return {
            "total_suggestions": total,
            "accepted_tags": sorted(accepted.items(), key=lambda x: x[1], reverse=True),
            "rejected_tags": sorted(rejected.items(), key=lambda x: x[1], reverse=True),
            "acceptance_rate": sum(accepted.values()) / total if total else 0.0,
        }
