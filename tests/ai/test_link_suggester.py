"""Comprehensive tests for link suggester module."""

import pytest
from memograph.ai.link_suggester import LinkSuggester, LinkSuggestion
from memograph import MemoryKernel


@pytest.fixture
async def populated_kernel(tmp_path):
    """Create a kernel with several interconnected notes."""
    kernel = MemoryKernel(str(tmp_path / "test_vault"))
    
    await kernel.remember_async(
        title="Python Basics",
        content="Python is a high-level programming language. It supports object-oriented programming and has simple syntax.",
        tags=['python', 'programming', 'basics']
    )
    
    await kernel.remember_async(
        title="Object-Oriented Programming",
        content="OOP is a programming paradigm based on objects. Python supports OOP with classes and inheritance.",
        tags=['oop', 'programming', 'concepts']
    )
    
    await kernel.remember_async(
        title="Data Structures",
        content="Common data structures include lists, dictionaries, sets, and tuples. Python provides built-in support for these.",
        tags=['datastructures', 'python']
    )
    
    await kernel.remember_async(
        title="Web Development",
        content="Web development with Python uses frameworks like Django and Flask. These help build web applications quickly.",
        tags=['web', 'python', 'frameworks']
    )
    
    await kernel.remember_async(
        title="Machine Learning",
        content="Machine learning in Python uses libraries like TensorFlow and scikit-learn. Python is popular for ML projects.",
        tags=['ml', 'python', 'ai']
    )
    
    kernel.ingest()
    return kernel


@pytest.fixture
def suggester(tmp_path):
    """Create a basic link suggester."""
    kernel = MemoryKernel(str(tmp_path / "test_vault"))
    return LinkSuggester(kernel, min_confidence=0.3, max_suggestions=10)


@pytest.fixture
async def suggester_populated(populated_kernel):
    """Create a link suggester with populated kernel."""
    return LinkSuggester(populated_kernel, min_confidence=0.3, max_suggestions=10)


# ============================================================================
# LinkSuggestion Dataclass Tests (3 tests)
# ============================================================================

class TestLinkSuggestion:
    """Test LinkSuggestion dataclass."""
    
    def test_create_suggestion(self):
        """Test creating a link suggestion."""
        suggestion = LinkSuggestion(
            target_title="Python Basics",
            target_id="python-basics",
            confidence=0.85,
            reason="Semantically similar",
            source="semantic"
        )
        
        assert suggestion.target_title == "Python Basics"
        assert suggestion.target_id == "python-basics"
        assert suggestion.confidence == 0.85
        assert suggestion.reason == "Semantically similar"
        assert suggestion.source == "semantic"
        assert suggestion.bidirectional is False
    
    def test_bidirectional_suggestion(self):
        """Test creating a bidirectional link suggestion."""
        suggestion = LinkSuggestion(
            target_title="Related Note",
            target_id="related",
            confidence=0.7,
            reason="Mentions this note",
            source="bidirectional",
            bidirectional=True
        )
        
        assert suggestion.bidirectional is True
    
    def test_suggestion_all_fields(self):
        """Test creating suggestion with all fields."""
        suggestion = LinkSuggestion(
            target_title="Test Note",
            target_id="test-123",
            confidence=0.95,
            reason="Multiple indicators",
            source="semantic,keywords",
            bidirectional=True
        )
        
        assert suggestion.source == "semantic,keywords"
        assert suggestion.bidirectional is True


# ============================================================================
# Initialization Tests (3 tests)
# ============================================================================

class TestInitialization:
    """Test LinkSuggester initialization."""
    
    def test_default_initialization(self, tmp_path):
        """Test initialization with default parameters."""
        kernel = MemoryKernel(str(tmp_path / "test"))
        suggester = LinkSuggester(kernel)
        
        assert suggester.kernel is kernel
        assert suggester.min_confidence == 0.4
        assert suggester.max_suggestions == 10
        assert isinstance(suggester._link_history, dict)
        assert len(suggester._link_history) == 0
    
    def test_custom_initialization(self, tmp_path):
        """Test initialization with custom parameters."""
        kernel = MemoryKernel(str(tmp_path / "test"))
        suggester = LinkSuggester(kernel, min_confidence=0.6, max_suggestions=5)
        
        assert suggester.min_confidence == 0.6
        assert suggester.max_suggestions == 5
    
    def test_edge_case_parameters(self, tmp_path):
        """Test initialization with edge case parameters."""
        kernel = MemoryKernel(str(tmp_path / "test"))
        
        suggester1 = LinkSuggester(kernel, min_confidence=0.0, max_suggestions=1)
        assert suggester1.min_confidence == 0.0
        assert suggester1.max_suggestions == 1
        
        suggester2 = LinkSuggester(kernel, min_confidence=1.0, max_suggestions=100)
        assert suggester2.min_confidence == 1.0
        assert suggester2.max_suggestions == 100


# ============================================================================
# Extract Wikilinks Tests (6 tests)
# ============================================================================

class TestExtractWikilinks:
    """Test wikilink extraction."""
    
    def test_extract_basic_wikilinks(self, suggester):
        """Test extracting basic wikilinks."""
        content = "See [[Python Basics]] and [[Object-Oriented Programming]] for more."
        links = suggester._extract_wikilinks(content)
        
        assert len(links) == 2
        assert "Python Basics" in links
        assert "Object-Oriented Programming" in links
    
    def test_extract_with_display_text(self, suggester):
        """Test extracting wikilinks with custom display text."""
        content = "See [[Python Basics|Python]] and [[Object-Oriented Programming|OOP]]."
        links = suggester._extract_wikilinks(content)
        
        assert "Python Basics" in links
        assert "Object-Oriented Programming" in links
    
    def test_extract_empty(self, suggester):
        """Test extracting wikilinks from content with no links."""
        content = "This is just regular text without any wikilinks."
        links = suggester._extract_wikilinks(content)
        
        assert len(links) == 0
    
    def test_extract_multiple_same(self, suggester):
        """Test extracting multiple references to same link."""
        content = "[[Python Basics]] is great. I love [[Python Basics]]."
        links = suggester._extract_wikilinks(content)
        
        assert "Python Basics" in links
    
    def test_extract_special_characters(self, suggester):
        """Test extracting wikilinks with special characters."""
        content = "See [[C++ Programming]] and [[Node.js Guide]]."
        links = suggester._extract_wikilinks(content)
        
        assert "C++ Programming" in links
        assert "Node.js Guide" in links
    
    def test_extract_nested_brackets(self, suggester):
        """Test with malformed brackets."""
        content = "[[Valid Link]] and [[[Invalid]] and [[Another Valid]]"
        links = suggester._extract_wikilinks(content)
        
        assert "Valid Link" in links
        assert "Another Valid" in links


# ============================================================================
# Main suggest_links Tests (11 tests)
# ============================================================================

class TestSuggestLinks:
    """Test main suggest_links method."""
    
    @pytest.mark.asyncio
    async def test_basic(self, suggester_populated):
        """Test basic link suggestion."""
        content = "I'm learning about Python programming and classes."
        suggestions = await suggester_populated.suggest_links(content, title="Learning Python")
        
        assert len(suggestions) > 0
        assert all(isinstance(s, LinkSuggestion) for s in suggestions)
        assert all(s.confidence >= 0.3 for s in suggestions)
        assert all(s.confidence <= 1.0 for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_empty_content(self, suggester_populated):
        """Test with empty content."""
        suggestions = await suggester_populated.suggest_links("", title="Empty Note")
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_excludes_existing_param(self, suggester_populated):
        """Test that suggestions exclude existing links from parameter."""
        content = "Python programming and classes."
        existing = ["Python Basics", "Data Structures"]
        
        suggestions = await suggester_populated.suggest_links(
            content, title="Learning", existing_links=existing
        )
        
        for suggestion in suggestions:
            assert suggestion.target_title not in existing
    
    @pytest.mark.asyncio
    async def test_excludes_existing_content(self, suggester_populated):
        """Test that existing wikilinks in content are excluded."""
        content = "I'm learning [[Python Basics]] and [[Web Development]]."
        suggestions = await suggester_populated.suggest_links(content, title="Learning")
        
        titles = [s.target_title for s in suggestions]
        assert "Python Basics" not in titles
        assert "Web Development" not in titles
    
    @pytest.mark.asyncio
    async def test_respects_max_suggestions(self, suggester_populated):
        """Test that max_suggestions limit is respected."""
        suggester_populated.max_suggestions = 3
        
        content = "Python programming data structures web development."
        suggestions = await suggester_populated.suggest_links(content, title="Guide")
        
        assert len(suggestions) <= 3
    
    @pytest.mark.asyncio
    async def test_respects_min_confidence(self, suggester_populated):
        """Test that min_confidence filter works."""
        suggester_populated.min_confidence = 0.8
        
        content = "Some vague content."
        suggestions = await suggester_populated.suggest_links(content, title="Vague")
        
        assert all(s.confidence >= 0.8 for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_sorted_by_confidence(self, suggester_populated):
        """Test that suggestions are sorted by confidence."""
        content = "Python machine learning data web"
        suggestions = await suggester_populated.suggest_links(content, title="Topics")
        
        if len(suggestions) > 1:
            confidences = [s.confidence for s in suggestions]
            assert confidences == sorted(confidences, reverse=True)
    
    @pytest.mark.asyncio
    async def test_with_note_id(self, suggester_populated):
        """Test suggestions with note_id for graph-based suggestions."""
        content = "More about Python."
        nodes = list(suggester_populated.kernel.graph.all_nodes())
        if nodes:
            note_id = nodes[0].id
            suggestions = await suggester_populated.suggest_links(
                content, title="Related", note_id=note_id
            )
            assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_with_title_only(self, suggester_populated):
        """Test with title but minimal content."""
        suggestions = await suggester_populated.suggest_links(
            content="Brief.", title="Python Machine Learning Tutorial"
        )
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_none_existing_links(self, suggester_populated):
        """Test with None as existing_links parameter."""
        suggestions = await suggester_populated.suggest_links(
            "Python content", title="Test", existing_links=None
        )
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_suggestion_structure(self, suggester_populated):
        """Test that suggestions have all required fields."""
        suggestions = await suggester_populated.suggest_links(
            "Python programming", title="Test"
        )
        
        for suggestion in suggestions:
            assert hasattr(suggestion, 'target_title')
            assert hasattr(suggestion, 'target_id')
            assert hasattr(suggestion, 'confidence')
            assert hasattr(suggestion, 'reason')
            assert hasattr(suggestion, 'source')
            assert hasattr(suggestion, 'bidirectional')


# ============================================================================
# _suggest_from_semantics Tests (5 tests)
# ============================================================================

class TestSuggestFromSemantics:
    """Test semantic similarity suggestions."""
    
    @pytest.mark.asyncio
    async def test_basic(self, suggester_populated):
        """Test basic semantic suggestions."""
        content = "Object-oriented programming with classes and inheritance"
        suggestions = await suggester_populated._suggest_from_semantics(content, "OOP")
        
        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert suggestion.source == "semantic"
            assert 0.0 < suggestion.confidence <= 0.95
    
    @pytest.mark.asyncio
    async def test_empty_content(self, suggester_populated):
        """Test semantic suggestions with empty content."""
        suggestions = await suggester_populated._suggest_from_semantics("", "")
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_confidence_decay(self, suggester_populated):
        """Test that confidence decays for lower-ranked results."""
        content = "Python programming language features"
        suggestions = await suggester_populated._suggest_from_semantics(content, "Python")
        
        if len(suggestions) > 1:
            confidences = [s.confidence for s in suggestions]
            assert confidences[0] >= confidences[-1]
    
    @pytest.mark.asyncio
    async def test_reason_format(self, suggester_populated):
        """Test that semantic suggestions have correct reason."""
        content = "Machine learning and data science"
        suggestions = await suggester_populated._suggest_from_semantics(content, "")
        
        for suggestion in suggestions:
            assert suggestion.reason == "Semantically similar content"
    
    @pytest.mark.asyncio
    async def test_no_embeddings(self, tmp_path):
        """Test semantic suggestions when embeddings aren't available."""
        kernel = MemoryKernel(str(tmp_path / "test"))
        suggester = LinkSuggester(kernel)
        suggestions = await suggester._suggest_from_semantics("content", "title")
        assert isinstance(suggestions, list)


# ============================================================================
# _suggest_from_keywords Tests (5 tests)
# ============================================================================

class TestSuggestFromKeywords:
    """Test keyword-based suggestions."""
    
    @pytest.mark.asyncio
    async def test_basic(self, suggester_populated):
        """Test basic keyword suggestions."""
        content = "Python is great for machine learning and data structures."
        suggestions = await suggester_populated._suggest_from_keywords(content)
        
        assert len(suggestions) > 0
        assert all(s.source == "keywords" for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_empty_graph(self, suggester):
        """Test with empty graph."""
        suggestions = await suggester._suggest_from_keywords("python")
        assert len(suggestions) == 0


# ============================================================================
# _suggest_from_graph, _suggest_bidirectional, Other Methods Tests (25 tests)
# ============================================================================

class TestOtherMethods:
    """Test remaining methods."""
    
    @pytest.mark.asyncio
    async def test_suggest_from_graph_with_id(self, suggester_populated):
        """Test graph suggestions with valid ID."""
        nodes = list(suggester_populated.kernel.graph.all_nodes())
        if nodes:
            suggestions = await suggester_populated._suggest_from_graph(nodes[0].id, "test")
            assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_suggest_bidirectional(self, suggester_populated):
        """Test bidirectional suggestions."""
        suggestions = await suggester_populated._suggest_bidirectional("python", "Python")
        assert isinstance(suggestions, list)
        for s in suggestions:
            assert s.bidirectional is True
    
    def test_merge_no_duplicates(self, suggester):
        """Test merging unique suggestions."""
        suggs = [
            LinkSuggestion("A", "a", 0.7, "R1", "semantic"),
            LinkSuggestion("B", "b", 0.6, "R2", "keywords")
        ]
        merged = suggester._merge_suggestions(suggs)
        assert len(merged) == 2
    
    def test_merge_with_duplicates(self, suggester):
        """Test merging duplicates."""
        suggs = [
            LinkSuggestion("A", "a", 0.7, "R1", "semantic"),
            LinkSuggestion("A", "a", 0.6, "R2", "keywords")
        ]
        merged = suggester._merge_suggestions(suggs)
        assert len(merged) == 1
        assert merged[0].confidence > 0.6
    
    def test_apply_history_no_history(self, suggester):
        """Test apply history with no feedback."""
        suggs = [LinkSuggestion("A", "a", 0.5, "R", "semantic")]
        adjusted = suggester._apply_history(suggs)
        assert adjusted[0].confidence == 0.5
    
    def test_apply_history_boost(self, suggester):
        """Test confidence boost from positive feedback."""
        suggester.record_feedback("A", True)
        suggester.record_feedback("A", True)
        suggs = [LinkSuggestion("A", "a", 0.5, "R", "semantic")]
        adjusted = suggester._apply_history(suggs)
        assert adjusted[0].confidence > 0.5
    
    def test_apply_history_reduce(self, suggester):
        """Test confidence reduction from negative feedback."""
        suggester.record_feedback("B", False)
        suggester.record_feedback("B", False)
        suggs = [LinkSuggestion("B", "b", 0.5, "R", "semantic")]
        adjusted = suggester._apply_history(suggs)
        assert adjusted[0].confidence < 0.5
    
    def test_record_feedback_accept(self, suggester):
        """Test recording accepted link."""
        suggester.record_feedback("A", True)
        assert suggester._link_history["A"]["accepted"] == 1
        assert suggester._link_history["A"]["rejected"] == 0
    
    def test_record_feedback_reject(self, suggester):
        """Test recording rejected link."""
        suggester.record_feedback("B", False)
        assert suggester._link_history["B"]["rejected"] == 1
    
    def test_record_feedback_multiple(self, suggester):
        """Test multiple feedback recordings."""
        suggester.record_feedback("C", True)
        suggester.record_feedback("C", True)
        suggester.record_feedback("C", False)
        assert suggester._link_history["C"]["accepted"] == 2
        assert suggester._link_history["C"]["rejected"] == 1
    
    def test_get_stats_empty(self, suggester):
        """Test stats with no history."""
        stats = suggester.get_link_stats()
        assert stats['total_suggestions'] == 0
        assert stats['accepted_links'] == []
        assert stats['rejected_links'] == []
        assert stats['acceptance_rate'] == 0.0
    
    def test_get_stats_only_accepted(self, suggester):
        """Test stats with only accepts."""
        suggester.record_feedback("A", True)
        suggester.record_feedback("B", True)
        stats = suggester.get_link_stats()
        assert stats['total_suggestions'] == 2
        assert len(stats['accepted_links']) == 2
        assert stats['acceptance_rate'] == 1.0
    
    def test_get_stats_only_rejected(self, suggester):
        """Test stats with only rejects."""
        suggester.record_feedback("A", False)
        suggester.record_feedback("B", False)
        stats = suggester.get_link_stats()
        assert stats['total_suggestions'] == 2
        assert len(stats['rejected_links']) == 2
        assert stats['acceptance_rate'] == 0.0
    
    def test_get_stats_mixed(self, suggester):
        """Test stats with mixed feedback."""
        suggester.record_feedback("A", True)
        suggester.record_feedback("A", True)
        suggester.record_feedback("B", False)
        suggester.record_feedback("C", True)
        stats = suggester.get_link_stats()
        assert stats['total_suggestions'] == 4
        assert stats['acceptance_rate'] == 0.75
    
    def test_get_stats_sorted(self, suggester):
        """Test that stats are sorted by count."""
        suggester.record_feedback("A", True)
        suggester.record_feedback("A", True)
        suggester.record_feedback("A", True)
        suggester.record_feedback("B", True)
        stats = suggester.get_link_stats()
        accepted = stats['accepted_links']
        if len(accepted) > 1:
            assert accepted[0][1] >= accepted[1][1]


# ============================================================================
# Integration & Edge Cases (10 tests)
# ============================================================================

class TestIntegrationAndEdgeCases:
    """Test integration scenarios and edge cases."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, suggester_populated):
        """Test complete workflow from suggestion to feedback."""
        content = "Python machine learning project"
        suggestions = await suggester_populated.suggest_links(content, title="ML Project")
        
        assert isinstance(suggestions, list)
        if suggestions:
            # Record feedback
            suggester_populated.record_feedback(suggestions[0].target_title, True)
            stats = suggester_populated.get_link_stats()
            assert stats['total_suggestions'] >= 1
    
    @pytest.mark.asyncio
    async def test_empty_vault(self, suggester):
        """Test with empty vault."""
        suggestions = await suggester.suggest_links("content", title="Test")
        assert isinstance(suggestions, list)
        assert len(suggestions) == 0
    
    @pytest.mark.asyncio
    async def test_very_long_content(self, suggester_populated):
        """Test with very long content."""
        content = "Python " * 1000
        suggestions = await suggester_populated.suggest_links(content, title="Long")
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_special_characters(self, suggester_populated):
        """Test with special characters."""
        content = "Python & C++ #programming @mentions"
        suggestions = await suggester_populated.suggest_links(content, title="Special")
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_unicode_content(self, suggester_populated):
        """Test with unicode content."""
        content = "Python プログラミング 编程"
        suggestions = await suggester_populated.suggest_links(content, title="Unicode")
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_only_title_no_content(self, suggester_populated):
        """Test with only title."""
        suggestions = await suggester_populated.suggest_links("", title="Python Programming")
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_all_links_filtered(self, suggester_populated):
        """Test when all potential links are already existing."""
        nodes = list(suggester_populated.kernel.graph.all_nodes())
        existing = [n.title for n in nodes if hasattr(n, 'title')]
        
        suggestions = await suggester_populated.suggest_links(
            "Python content", title="Test", existing_links=existing
        )
        # Should have few or no suggestions since all are filtered
        assert isinstance(suggestions, list)
    
    @pytest.mark.asyncio
    async def test_confidence_boundaries(self, suggester_populated):
        """Test that all confidences are within valid range."""
        suggestions = await suggester_populated.suggest_links(
            "Python programming", title="Test"
        )
        for s in suggestions:
            assert 0.0 <= s.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_multiple_sources_combined(self, suggester_populated):
        """Test suggestions from multiple sources."""
        content = "Python programming with machine learning and data structures"
        suggestions = await suggester_populated.suggest_links(content, title="Python ML")
        
        # Should get suggestions from various sources
        if suggestions:
            sources = set(s.source for s in suggestions)
            # May have multiple sources combined
            assert len(sources) > 0
    
    @pytest.mark.asyncio
    async def test_note_id_with_no_neighbors(self, suggester_populated):
        """Test graph suggestions for isolated note."""
        # Create isolated note
        await suggester_populated.kernel.remember_async(
            title="Isolated Note",
            content="This note has no connections",
            tags=['isolated']
        )
        suggester_populated.kernel.ingest()
        
        nodes = [n for n in suggester_populated.kernel.graph.all_nodes()
                if hasattr(n, 'title') and n.title == "Isolated Note"]
        if nodes:
            note_id = nodes[0].id
            suggestions = await suggester_populated._suggest_from_graph(note_id, "content")
            # May have no graph-based suggestions for isolated note
            assert isinstance(suggestions, list)