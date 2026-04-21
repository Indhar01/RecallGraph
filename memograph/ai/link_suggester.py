"""Automatic link suggestion for notes using semantic similarity and graph analysis."""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from memograph.ai.content_analyzer import ContentAnalyzer
import re


@dataclass
class LinkSuggestion:
    """Represents a suggested wikilink to another note."""
    target_title: str
    target_id: str
    confidence: float
    reason: str
    source: str
    bidirectional: bool = False  # True if the target should also link back


class LinkSuggester:
    """Suggest wikilinks between notes using semantic similarity and graph analysis."""
    
    def __init__(self, kernel, min_confidence: float = 0.4, max_suggestions: int = 10):
        """
        Initialize the link suggester.
        
        Args:
            kernel: MemoryKernel instance
            min_confidence: Minimum confidence score for suggestions (0.0-1.0)
            max_suggestions: Maximum number of suggestions to return
        """
        self.kernel = kernel
        self.analyzer = ContentAnalyzer(kernel)
        self.min_confidence = min_confidence
        self.max_suggestions = max_suggestions
        self._link_history: Dict[str, Dict[str, int]] = {}  # track accepted/rejected links
    
    async def suggest_links(
        self, 
        content: str, 
        title: str = "", 
        note_id: Optional[str] = None,
        existing_links: Optional[List[str]] = None
    ) -> List[LinkSuggestion]:
        """
        Suggest wikilinks for a note.
        
        Args:
            content: Note content
            title: Note title
            note_id: Optional note ID for graph-based suggestions
            existing_links: List of existing wikilink targets to exclude
        
        Returns:
            List of LinkSuggestion objects sorted by confidence
        """
        existing_links = existing_links or []
        existing_links_set = set(existing_links)
        
        # Extract existing wikilinks from content
        content_links = self._extract_wikilinks(content)
        existing_links_set.update(content_links)
        
        suggestions = []
        
        # Add suggestions from different sources
        suggestions.extend(await self._suggest_from_semantics(content, title))
        suggestions.extend(await self._suggest_from_keywords(content))
        suggestions.extend(await self._suggest_from_graph(note_id, content))
        suggestions.extend(await self._suggest_bidirectional(content, title))
        
        # Filter out existing links and low confidence
        suggestions = [
            s for s in suggestions 
            if s.target_title not in existing_links_set 
            and s.confidence >= self.min_confidence
        ]
        
        # Merge duplicate suggestions
        suggestions = self._merge_suggestions(suggestions)
        
        # Apply learning from history
        suggestions = self._apply_history(suggestions)
        
        # Sort by confidence and limit
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:self.max_suggestions]
    
    def _extract_wikilinks(self, content: str) -> List[str]:
        """Extract existing wikilink targets from content."""
        pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
        return pattern.findall(content)
    
    async def _suggest_from_semantics(self, content: str, title: str) -> List[LinkSuggestion]:
        """Suggest links using semantic similarity search."""
        suggestions = []
        
        try:
            # Use title and first 500 chars for semantic search
            query = f"{title}\n\n{content[:500]}"
            similar_nodes = await self.kernel.retrieve_nodes_async(query=query, top_k=15)
            
            for node in similar_nodes:
                node_title = getattr(node, 'title', getattr(node, 'id', 'Unknown'))
                node_id = getattr(node, 'id', node_title)
                
                # Calculate confidence based on retrieval score
                # retrieve_nodes_async returns nodes sorted by relevance
                # We'll use a decaying confidence for ranked results
                confidence = 0.9 / (similar_nodes.index(node) + 1)
                confidence = min(confidence, 0.95)
                
                suggestions.append(LinkSuggestion(
                    target_title=node_title,
                    target_id=node_id,
                    confidence=confidence,
                    reason="Semantically similar content",
                    source="semantic"
                ))
        except Exception as e:
            # If semantic search fails (no embeddings), continue with other methods
            pass
        
        return suggestions
    
    async def _suggest_from_keywords(self, content: str) -> List[LinkSuggestion]:
        """Suggest links based on keyword matching with note titles."""
        suggestions = []
        
        # Extract important keywords
        keywords = self.analyzer.extract_keywords(content, max_keywords=20, min_frequency=1)
        keyword_set = set(kw.lower() for kw, _ in keywords)
        
        # Get all notes from the graph
        all_nodes = list(self.kernel.graph.all_nodes())
        
        for node in all_nodes:
            node_title = getattr(node, 'title', getattr(node, 'id', 'Unknown'))
            node_id = getattr(node, 'id', node_title)
            
            # Check if note title matches keywords
            title_lower = node_title.lower()
            title_words = set(re.findall(r'\b\w+\b', title_lower))
            
            # Calculate overlap
            overlap = keyword_set & title_words
            if overlap:
                confidence = min(len(overlap) / 5.0, 0.8)  # Cap at 0.8
                suggestions.append(LinkSuggestion(
                    target_title=node_title,
                    target_id=node_id,
                    confidence=confidence,
                    reason=f"Matches keywords: {', '.join(list(overlap)[:3])}",
                    source="keywords"
                ))
        
        return suggestions
    
    async def _suggest_from_graph(self, note_id: Optional[str], content: str) -> List[LinkSuggestion]:
        """Suggest links based on graph neighborhood analysis."""
        if not note_id:
            return []
        
        suggestions = []
        
        try:
            # Get the node from graph
            node = self.kernel.graph.get_node(note_id)
            if not node:
                return []
            
            # Get neighbors (directly connected notes)
            neighbors = self.kernel.graph.get_neighbors(note_id)
            
            # Suggest neighbors of neighbors (2-hop connections)
            second_hop_nodes = set()
            for neighbor_id in neighbors:
                neighbor_neighbors = self.kernel.graph.get_neighbors(neighbor_id)
                second_hop_nodes.update(neighbor_neighbors)
            
            # Remove self and direct neighbors
            second_hop_nodes.discard(note_id)
            second_hop_nodes -= set(neighbors)
            
            # Create suggestions for 2-hop connections
            for target_id in second_hop_nodes:
                target_node = self.kernel.graph.get_node(target_id)
                if target_node:
                    target_title = getattr(target_node, 'title', target_id)
                    
                    # Count common neighbors (triadic closure)
                    target_neighbors = set(self.kernel.graph.get_neighbors(target_id))
                    common_neighbors = set(neighbors) & target_neighbors
                    
                    if common_neighbors:
                        confidence = min(len(common_neighbors) / 3.0, 0.75)
                        suggestions.append(LinkSuggestion(
                            target_title=target_title,
                            target_id=target_id,
                            confidence=confidence,
                            reason=f"Connected through {len(common_neighbors)} common notes",
                            source="graph"
                        ))
        
        except Exception:
            pass
        
        return suggestions
    
    async def _suggest_bidirectional(self, content: str, title: str) -> List[LinkSuggestion]:
        """Suggest notes that should link to this note (backlinks)."""
        suggestions = []
        
        # Extract key terms from title and content
        title_words = set(re.findall(r'\b\w{4,}\b', title.lower()))
        keywords = self.analyzer.extract_keywords(content, max_keywords=10)
        keyword_set = set(kw.lower() for kw, _ in keywords)
        
        important_terms = title_words | keyword_set
        
        # Find notes that mention these terms but don't link here
        all_nodes = list(self.kernel.graph.all_nodes())
        
        for node in all_nodes:
            node_content = getattr(node, 'content', '')
            node_title = getattr(node, 'title', getattr(node, 'id', 'Unknown'))
            node_id = getattr(node, 'id', node_title)
            
            if not node_content:
                continue
            
            # Check if node content mentions important terms
            content_lower = node_content.lower()
            content_words = set(re.findall(r'\b\w+\b', content_lower))
            
            matches = important_terms & content_words
            
            # Check if it doesn't already link to this note
            existing_links = self._extract_wikilinks(node_content)
            if title not in existing_links and matches:
                confidence = min(len(matches) / 5.0, 0.7)
                suggestions.append(LinkSuggestion(
                    target_title=node_title,
                    target_id=node_id,
                    confidence=confidence,
                    reason=f"Mentions: {', '.join(list(matches)[:3])}",
                    source="bidirectional",
                    bidirectional=True
                ))
        
        return suggestions
    
    def _merge_suggestions(self, suggestions: List[LinkSuggestion]) -> List[LinkSuggestion]:
        """Merge duplicate suggestions from different sources."""
        target_map: Dict[str, List[LinkSuggestion]] = {}
        
        for suggestion in suggestions:
            key = suggestion.target_id
            target_map.setdefault(key, []).append(suggestion)
        
        merged = []
        for target_id, slist in target_map.items():
            if len(slist) == 1:
                merged.append(slist[0])
            else:
                # Combine confidence scores (average with bonus for multiple sources)
                avg_confidence = sum(s.confidence for s in slist) / len(slist)
                # Bonus for multiple sources (up to 20% boost, capped at 1.0)
                multiplier = 1.0 + (len(slist) - 1) * 0.1
                combined_confidence = min(avg_confidence * multiplier, 1.0)
                
                # Take the best reason and combine sources
                best_suggestion = max(slist, key=lambda s: s.confidence)
                sources = ','.join(sorted(set(s.source for s in slist)))
                
                # Check if any suggestion is bidirectional
                is_bidirectional = any(s.bidirectional for s in slist)
                
                merged.append(LinkSuggestion(
                    target_title=best_suggestion.target_title,
                    target_id=target_id,
                    confidence=combined_confidence,
                    reason=best_suggestion.reason,
                    source=sources,
                    bidirectional=is_bidirectional
                ))
        
        return merged
    
    def _apply_history(self, suggestions: List[LinkSuggestion]) -> List[LinkSuggestion]:
        """Adjust confidence based on user feedback history."""
        if not self._link_history:
            return suggestions
        
        adjusted = []
        for suggestion in suggestions:
            target = suggestion.target_title
            
            if target in self._link_history:
                history = self._link_history[target]
                accepted = history.get('accepted', 0)
                rejected = history.get('rejected', 0)
                total = accepted + rejected
                
                if total > 0:
                    acceptance_rate = accepted / total
                    # Adjust confidence: boost if historically accepted, reduce if rejected
                    adjustment = (acceptance_rate - 0.5) * 0.2  # -0.1 to +0.1
                    new_confidence = max(0.0, min(1.0, suggestion.confidence + adjustment))
                    
                    adjusted.append(LinkSuggestion(
                        target_title=suggestion.target_title,
                        target_id=suggestion.target_id,
                        confidence=new_confidence,
                        reason=suggestion.reason,
                        source=suggestion.source,
                        bidirectional=suggestion.bidirectional
                    ))
                    continue
            
            adjusted.append(suggestion)
        
        return adjusted
    
    def record_feedback(self, target_title: str, accepted: bool):
        """Record user feedback on a link suggestion."""
        if target_title not in self._link_history:
            self._link_history[target_title] = {'accepted': 0, 'rejected': 0}
        
        if accepted:
            self._link_history[target_title]['accepted'] += 1
        else:
            self._link_history[target_title]['rejected'] += 1
    
    def get_link_stats(self) -> Dict[str, Any]:
        """Get statistics about link suggestions and feedback."""
        if not self._link_history:
            return {
                'total_suggestions': 0,
                'accepted_links': [],
                'rejected_links': [],
                'acceptance_rate': 0.0
            }
        
        accepted_links = []
        rejected_links = []
        total_accepted = 0
        total_rejected = 0
        
        for target, history in self._link_history.items():
            accepted = history['accepted']
            rejected = history['rejected']
            
            if accepted > 0:
                accepted_links.append((target, accepted))
                total_accepted += accepted
            if rejected > 0:
                rejected_links.append((target, rejected))
                total_rejected += rejected
        
        total = total_accepted + total_rejected
        
        return {
            'total_suggestions': total,
            'accepted_links': sorted(accepted_links, key=lambda x: x[1], reverse=True),
            'rejected_links': sorted(rejected_links, key=lambda x: x[1], reverse=True),
            'acceptance_rate': total_accepted / total if total > 0 else 0.0
        }