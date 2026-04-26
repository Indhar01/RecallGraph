"""Knowledge gap detection for identifying missing topics and incomplete areas."""

from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from collections import Counter
from memograph.ai.content_analyzer import ContentAnalyzer
import re


@dataclass
class KnowledgeGap:
    """Represents a detected knowledge gap."""

    gap_type: str  # 'missing_topic', 'weak_coverage', 'isolated_note', 'missing_link'
    title: str
    description: str
    severity: float  # 0.0-1.0
    suggestions: List[str]
    related_notes: List[str]


@dataclass
class TopicCluster:
    """Represents a cluster of related topics."""

    name: str
    keywords: List[str]
    note_ids: List[str]
    size: int
    density: float  # 0.0-1.0, connectivity within cluster
    coverage: float  # 0.0-1.0, how well-documented


@dataclass
class LearningPath:
    """Represents a suggested learning path."""

    topic: str
    notes: List[Tuple[str, str]]  # (note_id, note_title)
    order: str  # 'linear', 'branching', 'circular'
    completeness: float  # 0.0-1.0
    missing_steps: List[str]


class GapDetector:
    """Detect knowledge gaps and incomplete areas in a knowledge base."""

    def __init__(
        self,
        kernel,
        min_cluster_size: int = 3,
        min_severity: float = 0.3,
        max_gaps: int = 20,
    ):
        """
        Initialize the gap detector.

        Args:
            kernel: MemoryKernel instance
            min_cluster_size: Minimum notes in a cluster
            min_severity: Minimum severity for gap reporting
            max_gaps: Maximum number of gaps to return
        """
        self.kernel = kernel
        self.analyzer = ContentAnalyzer(kernel)
        self.min_cluster_size = min_cluster_size
        self.min_severity = min_severity
        self.max_gaps = max_gaps
        self._gap_history: Dict[str, int] = {}

    async def detect_gaps(self) -> List[KnowledgeGap]:
        """
        Detect all types of knowledge gaps in the knowledge base.

        Returns:
            List of KnowledgeGap objects sorted by severity
        """
        gaps = []

        # Detect different types of gaps
        gaps.extend(await self._detect_missing_topics())
        gaps.extend(await self._detect_weak_coverage())
        gaps.extend(self._detect_isolated_notes())
        gaps.extend(self._detect_missing_links())

        # Filter by minimum severity
        gaps = [g for g in gaps if g.severity >= self.min_severity]

        # Sort by severity and limit
        gaps.sort(key=lambda x: x.severity, reverse=True)
        return gaps[: self.max_gaps]

    async def _detect_missing_topics(self) -> List[KnowledgeGap]:
        """Detect topics mentioned but not documented."""
        gaps = []
        all_nodes = list(self.kernel.graph.all_nodes())

        if len(all_nodes) < 5:
            return gaps  # Not enough data

        # Collect all keywords and tags from existing notes
        all_keywords = Counter()
        documented_topics = set()

        for node in all_nodes:
            title = getattr(node, "title", getattr(node, "id", "")).lower()
            content = getattr(node, "content", "")
            tags = getattr(node, "tags", [])

            documented_topics.add(title)
            documented_topics.update(t.lower() for t in tags)

            # Extract keywords
            keywords = self.analyzer.extract_keywords(
                content, max_keywords=20, min_frequency=1
            )
            for kw, freq in keywords:
                all_keywords[kw] += freq

        # Find frequently mentioned keywords that aren't documented
        for keyword, freq in all_keywords.most_common(50):
            if keyword not in documented_topics and freq >= 3:
                # Check if it's a significant topic (not in any note title)
                found_in_title = any(
                    keyword in getattr(n, "title", "").lower() for n in all_nodes
                )

                if not found_in_title:
                    # Find notes that mention this keyword
                    related_notes = [
                        getattr(n, "title", getattr(n, "id", "Unknown"))
                        for n in all_nodes
                        if keyword in getattr(n, "content", "").lower()
                    ]

                    if len(related_notes) >= 2:
                        severity = min(freq / 10.0, 1.0) * 0.8
                        gaps.append(
                            KnowledgeGap(
                                gap_type="missing_topic",
                                title=f"Missing note about '{keyword}'",
                                description=f"Term appears {freq}x across {len(related_notes)} notes but no dedicated note exists",
                                severity=severity,
                                suggestions=[
                                    f"Create a note titled '{keyword.title()}'",
                                    f"Link it to: {', '.join(related_notes[:3])}",
                                ],
                                related_notes=related_notes,
                            )
                        )

        return gaps

    async def _detect_weak_coverage(self) -> List[KnowledgeGap]:
        """Detect topics with shallow or incomplete coverage."""
        gaps = []
        all_nodes = list(self.kernel.graph.all_nodes())

        for node in all_nodes:
            title = getattr(node, "title", getattr(node, "id", "Unknown"))
            content = getattr(node, "content", "")

            # Analyze content depth
            structure = self.analyzer.analyze_structure(content)
            word_count = structure["word_count"]
            heading_count = structure["heading_count"]
            link_count = structure["link_count"]

            # Detect weak coverage indicators
            is_weak = False
            reasons = []
            suggestions = []

            # Too short
            if word_count < 100:
                is_weak = True
                reasons.append(f"only {word_count} words")
                suggestions.append("Expand with more details and examples")

            # No structure
            if word_count > 200 and heading_count == 0:
                is_weak = True
                reasons.append("no headings for organization")
                suggestions.append("Add section headings to organize content")

            # Isolated (no links)
            if link_count == 0 and word_count > 50:
                is_weak = True
                reasons.append("no links to other notes")
                suggestions.append("Add wikilinks to related concepts")

            # No tags
            tags = getattr(node, "tags", [])
            if not tags and word_count > 100:
                is_weak = True
                reasons.append("no tags for categorization")
                suggestions.append("Add relevant tags")

            if is_weak:
                # Calculate severity based on multiple factors
                severity = 0.5
                if word_count < 50:
                    severity += 0.2
                if link_count == 0:
                    severity += 0.15
                if not tags:
                    severity += 0.1
                severity = min(severity, 1.0)

                gaps.append(
                    KnowledgeGap(
                        gap_type="weak_coverage",
                        title=f"Weak coverage: {title}",
                        description=f"Note has {', '.join(reasons)}",
                        severity=severity,
                        suggestions=suggestions,
                        related_notes=[title],
                    )
                )

        return gaps

    def _detect_isolated_notes(self) -> List[KnowledgeGap]:
        """Detect notes with few or no connections."""
        gaps = []
        all_nodes = list(self.kernel.graph.all_nodes())

        for node in all_nodes:
            title = getattr(node, "title", getattr(node, "id", "Unknown"))
            node_id = getattr(node, "id", title)

            # Count connections
            try:
                neighbors = self.kernel.graph.neighbors(
                    node_id, depth=1, include_backlinks=True
                )
                connection_count = len(neighbors)
            except Exception:
                # Fallback: count links and backlinks manually
                node = self.kernel.graph.get(node_id)
                if node:
                    connection_count = len(node.links) + len(node.backlinks)
                else:
                    connection_count = 0

            if connection_count <= 1:
                # Find potential connections based on keywords
                content = getattr(node, "content", "")
                keywords = self.analyzer.extract_keywords(
                    content, max_keywords=10, min_frequency=1
                )

                # Find notes with similar keywords
                potential_connections = []
                for other_node in all_nodes:
                    other_id = getattr(other_node, "id", "")
                    if other_id == node_id:
                        continue

                    other_title = getattr(
                        other_node, "title", getattr(other_node, "id", "Unknown")
                    )
                    other_content = getattr(other_node, "content", "")

                    # Check for keyword overlap
                    for kw, _ in keywords:
                        if kw in other_content.lower() or kw in other_title.lower():
                            potential_connections.append(other_title)
                            break

                # Create gap even if no potential connections found (for truly isolated notes)
                severity = 0.7 if connection_count == 0 else 0.5
                
                if potential_connections:
                    suggestions = [
                        f"Add links to: {', '.join(potential_connections[:3])}",
                        "Review content for connection opportunities",
                    ]
                    related_notes = [title] + potential_connections[:5]
                else:
                    # Single note or truly isolated - provide general suggestions
                    suggestions = [
                        "Add links to related concepts when more notes are created",
                        "Add tags to help with future connections",
                        "Review content and expand with related topics",
                    ]
                    related_notes = [title]

                gaps.append(
                    KnowledgeGap(
                        gap_type="isolated_note",
                        title=f"Isolated note: {title}",
                        description=f"Note has only {connection_count} connection(s)",
                        severity=severity,
                        suggestions=suggestions,
                        related_notes=related_notes,
                    )
                )

        return gaps

    def _detect_missing_links(self) -> List[KnowledgeGap]:
        """Detect notes that should be linked but aren't."""
        gaps = []
        all_nodes = list(self.kernel.graph.all_nodes())

        # Build a map of note titles to IDs
        title_to_id = {
            getattr(n, "title", getattr(n, "id", "")): getattr(n, "id", "")
            for n in all_nodes
        }

        for node in all_nodes:
            title = getattr(node, "title", getattr(node, "id", "Unknown"))
            content = getattr(node, "content", "")
            node_id = getattr(node, "id", title)

            # Find mentions of other note titles in content
            missing_links = []

            for other_title, other_id in title_to_id.items():
                if other_id == node_id:
                    continue

                # Check if title is mentioned but not linked
                # Simple word boundary match
                pattern = r"\b" + re.escape(other_title.lower()) + r"\b"
                if re.search(pattern, content.lower()):
                    # Check if it's already linked
                    wikilink_pattern = r"\[\[" + re.escape(other_title) + r"[\]|]"
                    if not re.search(wikilink_pattern, content, re.IGNORECASE):
                        missing_links.append(other_title)

            if missing_links:
                severity = min(len(missing_links) / 5.0, 0.8)

                gaps.append(
                    KnowledgeGap(
                        gap_type="missing_link",
                        title=f"Missing links in: {title}",
                        description=f"Note mentions {len(missing_links)} other notes without linking",
                        severity=severity,
                        suggestions=[
                            f"Add wikilinks for: {', '.join(missing_links[:3])}",
                            "Use [[note title]] format for linking",
                        ],
                        related_notes=[title] + missing_links[:5],
                    )
                )

        return gaps

    async def cluster_topics(self) -> List[TopicCluster]:
        """
        Cluster notes by topic using keywords and semantic similarity.

        Returns:
            List of TopicCluster objects
        """
        all_nodes = list(self.kernel.graph.all_nodes())

        if len(all_nodes) < self.min_cluster_size:
            return []

        # Extract keywords from all notes
        note_keywords: Dict[str, Set[str]] = {}
        all_keywords = Counter()

        for node in all_nodes:
            node_id = getattr(node, "id", "")
            content = getattr(node, "content", "")
            tags = getattr(node, "tags", [])

            keywords = set(tags)
            extracted = self.analyzer.extract_keywords(
                content, max_keywords=10, min_frequency=1
            )
            keywords.update(kw for kw, _ in extracted)

            note_keywords[node_id] = keywords
            all_keywords.update(keywords)

        # Find dominant keywords (potential cluster names)
        dominant_keywords = [
            kw
            for kw, freq in all_keywords.most_common(20)
            if freq >= self.min_cluster_size
        ]

        # Create clusters based on keyword similarity
        clusters = []
        used_nodes = set()

        for keyword in dominant_keywords:
            cluster_nodes = []

            for node_id, keywords in note_keywords.items():
                if node_id in used_nodes:
                    continue

                if keyword in keywords:
                    cluster_nodes.append(node_id)
                    used_nodes.add(node_id)

            if len(cluster_nodes) >= self.min_cluster_size:
                # Calculate cluster metrics
                cluster_keywords = set()
                for node_id in cluster_nodes:
                    cluster_keywords.update(note_keywords[node_id])

                # Calculate density (internal connections)
                total_possible = len(cluster_nodes) * (len(cluster_nodes) - 1) / 2
                actual_connections = 0

                if total_possible > 0:
                    for i, node_id in enumerate(cluster_nodes):
                        try:
                            neighbors_list = self.kernel.graph.neighbors(
                                node_id, depth=1, include_backlinks=True
                            )
                            neighbor_ids = set(n.id for n in neighbors_list)
                            actual_connections += len(
                                neighbor_ids & set(cluster_nodes[i + 1 :])
                            )
                        except Exception:
                            # Fallback: use links directly
                            node = self.kernel.graph.get(node_id)
                            if node:
                                neighbor_ids = set(node.links + node.backlinks)
                                actual_connections += len(
                                    neighbor_ids & set(cluster_nodes[i + 1 :])
                                )

                    density = actual_connections / total_possible
                else:
                    density = 0.0

                # Calculate coverage (average word count)
                total_words = 0
                for node_id in cluster_nodes:
                    node = self.kernel.graph.get(node_id)
                    if node:
                        content = getattr(node, "content", "")
                        structure = self.analyzer.analyze_structure(content)
                        total_words += structure["word_count"]

                avg_words = total_words / len(cluster_nodes) if cluster_nodes else 0
                coverage = min(avg_words / 500.0, 1.0)  # 500+ words = full coverage

                clusters.append(
                    TopicCluster(
                        name=keyword.title(),
                        keywords=sorted(list(cluster_keywords))[:10],
                        note_ids=cluster_nodes,
                        size=len(cluster_nodes),
                        density=density,
                        coverage=coverage,
                    )
                )

        return clusters

    async def suggest_learning_paths(self, topic: str) -> List[LearningPath]:
        """
        Suggest learning paths for a given topic.

        Args:
            topic: The topic to create learning paths for

        Returns:
            List of LearningPath objects
        """
        all_nodes = list(self.kernel.graph.all_nodes())

        # Find notes related to the topic
        relevant_notes = []
        for node in all_nodes:
            title = getattr(node, "title", getattr(node, "id", "Unknown"))
            content = getattr(node, "content", "")
            tags = getattr(node, "tags", [])
            node_id = getattr(node, "id", title)

            # Check if note is related to topic
            topic_lower = topic.lower()
            if (
                topic_lower in title.lower()
                or topic_lower in content.lower()
                or any(topic_lower in tag.lower() for tag in tags)
            ):
                relevant_notes.append((node_id, title, content))

        if len(relevant_notes) < 2:
            return []

        paths = []

        # Create a linear path based on content depth
        linear_path = sorted(
            relevant_notes,
            key=lambda x: len(x[2]),  # Sort by content length
        )

        # Analyze path completeness
        total_words = sum(len(content) for _, _, content in linear_path)
        avg_words = total_words / len(linear_path)
        completeness = min(avg_words / 300.0, 1.0)

        # Identify missing steps
        missing_steps = []
        if len(linear_path) < 3:
            missing_steps.append("Add intermediate notes to fill gaps")
        if completeness < 0.5:
            missing_steps.append("Expand existing notes with more details")

        # Check for missing connections
        unconnected = []
        for i in range(len(linear_path) - 1):
            node_id = linear_path[i][0]
            next_id = linear_path[i + 1][0]
            try:
                neighbors_list = self.kernel.graph.neighbors(
                    node_id, depth=1, include_backlinks=True
                )
                neighbor_ids = [n.id for n in neighbors_list]
                if next_id not in neighbor_ids:
                    unconnected.append((linear_path[i][1], linear_path[i + 1][1]))
            except Exception:
                # Fallback: check links directly
                node = self.kernel.graph.get(node_id)
                if node and next_id not in (node.links + node.backlinks):
                    unconnected.append((linear_path[i][1], linear_path[i + 1][1]))

        if unconnected:
            missing_steps.append(
                f"Add links between: {', '.join(f'{a}->{b}' for a, b in unconnected[:2])}"
            )

        paths.append(
            LearningPath(
                topic=topic,
                notes=[(nid, title) for nid, title, _ in linear_path],
                order="linear",
                completeness=completeness,
                missing_steps=missing_steps,
            )
        )

        # Create a branching path if there are enough notes
        if len(relevant_notes) >= 5:
            # Group by depth (basic -> advanced)
            basic = [n for n in relevant_notes if len(n[2]) < 200]
            intermediate = [n for n in relevant_notes if 200 <= len(n[2]) < 500]
            advanced = [n for n in relevant_notes if len(n[2]) >= 500]

            if basic and (intermediate or advanced):
                branching_notes = basic[:1] + intermediate[:2] + advanced[:2]
                completeness_branching = 0.8 if intermediate and advanced else 0.5

                missing_branching = []
                if not intermediate:
                    missing_branching.append("Add intermediate-level notes")
                if not advanced:
                    missing_branching.append("Add advanced-level notes")

                paths.append(
                    LearningPath(
                        topic=topic,
                        notes=[(nid, title) for nid, title, _ in branching_notes],
                        order="branching",
                        completeness=completeness_branching,
                        missing_steps=missing_branching,
                    )
                )

        return paths

    def record_gap_feedback(self, gap_title: str, addressed: bool):
        """Record user feedback on a detected gap."""
        self._gap_history[gap_title] = self._gap_history.get(gap_title, 0) + (
            1 if addressed else -1
        )

    def get_gap_stats(self) -> Dict[str, Any]:
        """Get statistics about detected gaps and user feedback."""
        if not self._gap_history:
            return {
                "total_gaps": 0,
                "addressed_gaps": [],
                "ignored_gaps": [],
                "resolution_rate": 0.0,
            }

        addressed = {g: c for g, c in self._gap_history.items() if c > 0}
        ignored = {g: abs(c) for g, c in self._gap_history.items() if c < 0}
        total = sum(abs(c) for c in self._gap_history.values())

        return {
            "total_gaps": total,
            "addressed_gaps": sorted(
                addressed.items(), key=lambda x: x[1], reverse=True
            ),
            "ignored_gaps": sorted(ignored.items(), key=lambda x: x[1], reverse=True),
            "resolution_rate": sum(addressed.values()) / total if total else 0.0,
        }

    async def analyze_knowledge_base(self) -> Dict[str, Any]:
        """
        Perform comprehensive knowledge base analysis.

        Returns:
            Dictionary with gaps, clusters, and paths
        """
        gaps = await self.detect_gaps()
        clusters = await self.cluster_topics()

        # Find top topics for learning paths
        top_topics = []
        if clusters:
            # Get top 3 clusters by size
            top_clusters = sorted(clusters, key=lambda c: c.size, reverse=True)[:3]
            top_topics = [c.name for c in top_clusters]

        learning_paths = []
        for topic in top_topics:
            paths = await self.suggest_learning_paths(topic)
            learning_paths.extend(paths)

        return {
            "summary": {
                "total_gaps": len(gaps),
                "gap_types": Counter(g.gap_type for g in gaps),
                "avg_severity": sum(g.severity for g in gaps) / len(gaps)
                if gaps
                else 0.0,
                "total_clusters": len(clusters),
                "total_paths": len(learning_paths),
            },
            "gaps": [
                {
                    "type": g.gap_type,
                    "title": g.title,
                    "description": g.description,
                    "severity": round(g.severity, 2),
                    "suggestions": g.suggestions,
                    "related_notes": g.related_notes[:5],
                }
                for g in gaps
            ],
            "clusters": [
                {
                    "name": c.name,
                    "size": c.size,
                    "keywords": c.keywords[:5],
                    "density": round(c.density, 2),
                    "coverage": round(c.coverage, 2),
                }
                for c in clusters
            ],
            "learning_paths": [
                {
                    "topic": lp.topic,
                    "notes": lp.notes,
                    "order": lp.order,
                    "completeness": round(lp.completeness, 2),
                    "missing_steps": lp.missing_steps,
                }
                for lp in learning_paths
            ],
        }
