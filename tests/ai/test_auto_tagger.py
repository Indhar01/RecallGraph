"""Comprehensive tests for AutoTagger functionality."""

import pytest
from memograph.ai.auto_tagger import AutoTagger, TagSuggestion
from memograph import MemoryKernel


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def empty_kernel(tmp_path):
    """Create an empty kernel for testing."""
    return MemoryKernel(str(tmp_path / "empty_vault"))


@pytest.fixture
def populated_kernel(tmp_path):
    """Create a kernel with test memories."""
    kernel = MemoryKernel(str(tmp_path / "test_vault"))
    
    # Add memories with various tags
    kernel.remember(
        title="Python Basics",
        content="Python programming language basics. Variables, functions, classes.",
        tags=['python', 'programming', 'tutorial']
    )
    kernel.remember(
        title="Machine Learning",
        content="Machine learning with Python. Neural networks and deep learning.",
        tags=['python', 'ml', 'ai']
    )
    kernel.remember(
        title="Web Development",
        content="Web development with Flask and Django frameworks.",
        tags=['python', 'web', 'backend']
    )
    kernel.remember(
        title="Code Snippet",
        content="```python\ndef hello():\n    print('Hello')\n```\nUseful Python code.",
        tags=['code', 'python']
    )
    
    kernel.ingest()
    return kernel


@pytest.fixture
async def tagger(populated_kernel):
    """Create AutoTagger with populated kernel."""
    return AutoTagger(populated_kernel)


@pytest.fixture
def empty_tagger(empty_kernel):
    """Create AutoTagger with empty kernel."""
    return AutoTagger(empty_kernel)


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================

def test_init_default_parameters(empty_kernel):
    """Test AutoTagger initialization with default parameters."""
    tagger = AutoTagger(empty_kernel)
    
    assert tagger.kernel == empty_kernel
    assert tagger.min_confidence == 0.3
    assert tagger.max_suggestions == 5
    assert tagger.analyzer is not None
    assert isinstance(tagger._tag_history, dict)
    assert len(tagger._tag_history) == 0


def test_init_custom_parameters(empty_kernel):
    """Test AutoTagger initialization with custom parameters."""
    tagger = AutoTagger(empty_kernel, min_confidence=0.5, max_suggestions=10)
    
    assert tagger.min_confidence == 0.5
    assert tagger.max_suggestions == 10


def test_init_edge_case_parameters(empty_kernel):
    """Test AutoTagger with edge case parameters."""
    tagger = AutoTagger(empty_kernel, min_confidence=0.0, max_suggestions=1)
    
    assert tagger.min_confidence == 0.0
    assert tagger.max_suggestions == 1


# =============================================================================
# SUGGEST_TAGS TESTS (MAIN METHOD)
# =============================================================================

@pytest.mark.asyncio
async def test_suggest_tags_basic(tagger):
    """Test basic tag suggestion functionality."""
    suggestions = await tagger.suggest_tags("Python tutorial")
    
    assert isinstance(suggestions, list)
    assert all(isinstance(s, TagSuggestion) for s in suggestions)
    assert len(suggestions) <= tagger.max_suggestions


@pytest.mark.asyncio
async def test_suggest_tags_empty_content(tagger):
    """Test tag suggestion with empty content."""
    suggestions = await tagger.suggest_tags("")
    
    assert isinstance(suggestions, list)
    # May return empty or structure-based tags


@pytest.mark.asyncio
async def test_suggest_tags_with_existing_tags(tagger):
    """Test that existing tags are filtered out."""
    existing = ['python', 'programming']
    suggestions = await tagger.suggest_tags(
        "Python programming tutorial",
        existing_tags=existing
    )
    
    # None of the suggested tags should be in existing_tags
    for suggestion in suggestions:
        assert suggestion.tag not in existing


@pytest.mark.asyncio
async def test_suggest_tags_respects_min_confidence(empty_kernel):
    """Test that suggestions below min_confidence are filtered."""
    tagger = AutoTagger(empty_kernel, min_confidence=0.8)
    suggestions = await tagger.suggest_tags("test content")
    
    # All suggestions should meet minimum confidence
    for suggestion in suggestions:
        assert suggestion.confidence >= 0.8


@pytest.mark.asyncio
async def test_suggest_tags_respects_max_suggestions(tagger):
    """Test that suggestions are limited by max_suggestions."""
    tagger.max_suggestions = 2
    suggestions = await tagger.suggest_tags(
        "Python machine learning deep learning neural networks"
    )
    
    assert len(suggestions) <= 2


@pytest.mark.asyncio
async def test_suggest_tags_with_title(tagger):
    """Test tag suggestion with title parameter."""
    suggestions = await tagger.suggest_tags(
        "Python tutorial content",
        title="Advanced Python"
    )
    
    assert isinstance(suggestions, list)
    assert all(isinstance(s, TagSuggestion) for s in suggestions)


@pytest.mark.asyncio
async def test_suggest_tags_without_existing_tags_param(tagger):
    """Test that existing_tags parameter is optional."""
    suggestions = await tagger.suggest_tags("Python programming")
    
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_suggest_tags_sorted_by_confidence(tagger):
    """Test that suggestions are sorted by confidence descending."""
    suggestions = await tagger.suggest_tags(
        "Python machine learning tutorial programming"
    )
    
    if len(suggestions) > 1:
        for i in range(len(suggestions) - 1):
            assert suggestions[i].confidence >= suggestions[i + 1].confidence


# =============================================================================
# _suggest_from_frequency TESTS
# =============================================================================

def test_suggest_from_frequency_basic(tagger):
    """Test frequency-based tag suggestions."""
    content = "python python python machine learning learning"
    suggestions = tagger._suggest_from_frequency(content)
    
    assert isinstance(suggestions, list)
    assert all(isinstance(s, TagSuggestion) for s in suggestions)
    assert all(s.source == 'frequency' for s in suggestions)


def test_suggest_from_frequency_confidence_calculation(tagger):
    """Test that confidence is calculated as min(freq/10, 1.0) * 0.6."""
    content = "test " * 20  # High frequency
    suggestions = tagger._suggest_from_frequency(content)
    
    for suggestion in suggestions:
        assert 0 <= suggestion.confidence <= 0.6  # Max is 1.0 * 0.6


def test_suggest_from_frequency_reason_format(tagger):
    """Test that reason includes appearance count."""
    content = "python python python"
    suggestions = tagger._suggest_from_frequency(content)
    
    for suggestion in suggestions:
        assert "Appears" in suggestion.reason
        assert "x" in suggestion.reason


def test_suggest_from_frequency_empty_content(tagger):
    """Test frequency suggestions with empty content."""
    suggestions = tagger._suggest_from_frequency("")
    
    assert isinstance(suggestions, list)


# =============================================================================
# _suggest_from_semantics TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_suggest_from_semantics_basic(tagger):
    """Test semantic-based tag suggestions."""
    content = "Python programming tutorial"
    suggestions = await tagger._suggest_from_semantics(content)
    
    assert isinstance(suggestions, list)
    assert all(isinstance(s, TagSuggestion) for s in suggestions)
    assert all(s.source == 'semantic' for s in suggestions)


@pytest.mark.asyncio
async def test_suggest_from_semantics_confidence_calculation(tagger):
    """Test that confidence is calculated as similarity * 0.9."""
    content = "Machine learning with Python"
    suggestions = await tagger._suggest_from_semantics(content)
    
    for suggestion in suggestions:
        assert 0 <= suggestion.confidence <= 0.9  # Max is 1.0 * 0.9


@pytest.mark.asyncio
async def test_suggest_from_semantics_reason_format(tagger):
    """Test that reason includes similarity score."""
    content = "Python programming"
    suggestions = await tagger._suggest_from_semantics(content)
    
    for suggestion in suggestions:
        assert "Similar:" in suggestion.reason


@pytest.mark.asyncio
async def test_suggest_from_semantics_empty_content(tagger):
    """Test semantic suggestions with empty content."""
    suggestions = await tagger._suggest_from_semantics("")
    
    assert isinstance(suggestions, list)


# =============================================================================
# _suggest_from_structure TESTS
# =============================================================================

def test_suggest_from_structure_basic(tagger):
    """Test structure-based tag suggestions."""
    content = "Some basic content"
    suggestions = tagger._suggest_from_structure(content, "")
    
    assert isinstance(suggestions, list)
    assert len(suggestions) >= 1  # At least content type suggestion
    assert all(isinstance(s, TagSuggestion) for s in suggestions)


def test_suggest_from_structure_with_code_blocks(tagger):
    """Test structure suggestions with code blocks."""
    content = "```python\nprint('hello')\n```\nMore content\n```js\nconsole.log('hi');\n```"
    suggestions = tagger._suggest_from_structure(content, "")
    
    # Should have content type + code tag
    code_suggestions = [s for s in suggestions if s.tag == 'code']
    assert len(code_suggestions) > 0
    assert all(s.source == 'structure' for s in code_suggestions)


def test_suggest_from_structure_without_code_blocks(tagger):
    """Test structure suggestions without code blocks."""
    content = "Regular text without any code blocks"
    suggestions = tagger._suggest_from_structure(content, "")
    
    # Should not have code tag
    code_suggestions = [s for s in suggestions if s.tag == 'code']
    assert len(code_suggestions) == 0


def test_suggest_from_structure_with_title(tagger):
    """Test structure suggestions with title parameter."""
    content = "Content"
    suggestions = tagger._suggest_from_structure(content, "Test Title")
    
    assert isinstance(suggestions, list)
    # Title affects content type detection


def test_suggest_from_structure_confidence_values(tagger):
    """Test that structure suggestions have appropriate confidence."""
    content = "```python\ncode\n```"
    suggestions = tagger._suggest_from_structure(content, "")
    
    # Content type should have 0.8 confidence
    type_suggestions = [s for s in suggestions if s.source == 'structure' and s.tag != 'code']
    if type_suggestions:
        assert type_suggestions[0].confidence == 0.8
    
    # Code tag should have 0.7 confidence
    code_suggestions = [s for s in suggestions if s.tag == 'code']
    if code_suggestions:
        assert code_suggestions[0].confidence == 0.7


# =============================================================================
# _suggest_from_related_notes TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_suggest_from_related_notes_basic(tagger):
    """Test suggestions from related notes."""
    content = "Python programming tutorial"
    suggestions = await tagger._suggest_from_related_notes(content)
    
    assert isinstance(suggestions, list)
    assert all(isinstance(s, TagSuggestion) for s in suggestions)
    assert all(s.source == 'existing' for s in suggestions)


@pytest.mark.asyncio
async def test_suggest_from_related_notes_empty_kernel(empty_tagger):
    """Test related notes suggestions with empty kernel."""
    suggestions = await empty_tagger._suggest_from_related_notes("test content")
    
    # Should handle gracefully (empty list or exception caught)
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_suggest_from_related_notes_confidence_calculation(tagger):
    """Test confidence calculation for related notes."""
    content = "Python programming"
    suggestions = await tagger._suggest_from_related_notes(content)
    
    # Confidence should be (count/total) * 0.7
    for suggestion in suggestions:
        assert 0 <= suggestion.confidence <= 0.7


@pytest.mark.asyncio
async def test_suggest_from_related_notes_reason_format(tagger):
    """Test reason format for related notes suggestions."""
    content = "Python machine learning"
    suggestions = await tagger._suggest_from_related_notes(content)
    
    for suggestion in suggestions:
        assert "similar" in suggestion.reason.lower()
        assert "/" in suggestion.reason


# =============================================================================
# _merge_suggestions TESTS
# =============================================================================

def test_merge_suggestions_no_duplicates(tagger):
    """Test merging when there are no duplicate tags."""
    suggestions = [
        TagSuggestion('python', 0.5, 'reason1', 'source1'),
        TagSuggestion('java', 0.4, 'reason2', 'source2'),
        TagSuggestion('cpp', 0.3, 'reason3', 'source3')
    ]
    
    merged = tagger._merge_suggestions(suggestions)
    
    assert len(merged) == 3
    assert all(isinstance(s, TagSuggestion) for s in merged)


def test_merge_suggestions_with_duplicates(tagger):
    """Test merging duplicate tags with confidence boost."""
    suggestions = [
        TagSuggestion('python', 0.5, 'reason1', 'source1'),
        TagSuggestion('python', 0.6, 'reason2', 'source2'),
        TagSuggestion('java', 0.4, 'reason3', 'source3')
    ]
    
    merged = tagger._merge_suggestions(suggestions)
    
    assert len(merged) == 2  # python and java
    
    # Find the merged python suggestion
    python_suggestion = next(s for s in merged if s.tag == 'python')
    
    # Average confidence should be (0.5 + 0.6) / 2 = 0.55, then boosted by 1.2
    expected_conf = min((0.5 + 0.6) / 2 * 1.2, 1.0)
    assert abs(python_suggestion.confidence - expected_conf) < 0.01


def test_merge_suggestions_multiple_sources(tagger):
    """Test that multiple sources are combined."""
    suggestions = [
        TagSuggestion('python', 0.5, 'reason1', 'frequency'),
        TagSuggestion('python', 0.6, 'reason2', 'semantic'),
        TagSuggestion('python', 0.4, 'reason3', 'structure')
    ]
    
    merged = tagger._merge_suggestions(suggestions)
    
    assert len(merged) == 1
    assert 'frequency' in merged[0].source
    assert 'semantic' in merged[0].source
    assert 'structure' in merged[0].source


def test_merge_suggestions_best_reason_preserved(tagger):
    """Test that the best reason is preserved when merging."""
    suggestions = [
        TagSuggestion('python', 0.5, 'reason1', 'source1'),
        TagSuggestion('python', 0.8, 'best_reason', 'source2')
    ]
    
    merged = tagger._merge_suggestions(suggestions)
    
    assert len(merged) == 1
    assert merged[0].reason == 'best_reason'  # Highest confidence reason


def test_merge_suggestions_confidence_capped_at_one(tagger):
    """Test that boosted confidence doesn't exceed 1.0."""
    suggestions = [
        TagSuggestion('python', 0.9, 'reason1', 'source1'),
        TagSuggestion('python', 0.9, 'reason2', 'source2')
    ]
    
    merged = tagger._merge_suggestions(suggestions)
    
    assert len(merged) == 1
    assert merged[0].confidence <= 1.0


def test_merge_suggestions_empty_list(tagger):
    """Test merging an empty list."""
    merged = tagger._merge_suggestions([])
    
    assert merged == []


# =============================================================================
# RECORD_FEEDBACK TESTS
# =============================================================================

def test_record_feedback_accept_tag(tagger):
    """Test recording positive feedback for a tag."""
    tagger.record_feedback('python', True)
    
    assert 'python' in tagger._tag_history
    assert tagger._tag_history['python'] == 1


def test_record_feedback_reject_tag(tagger):
    """Test recording negative feedback for a tag."""
    tagger.record_feedback('java', False)
    
    assert 'java' in tagger._tag_history
    assert tagger._tag_history['java'] == -1


def test_record_feedback_multiple_accepts(tagger):
    """Test recording multiple accepts for same tag."""
    tagger.record_feedback('python', True)
    tagger.record_feedback('python', True)
    tagger.record_feedback('python', True)
    
    assert tagger._tag_history['python'] == 3


def test_record_feedback_multiple_rejects(tagger):
    """Test recording multiple rejects for same tag."""
    tagger.record_feedback('java', False)
    tagger.record_feedback('java', False)
    
    assert tagger._tag_history['java'] == -2


def test_record_feedback_mixed_feedback(tagger):
    """Test recording mixed feedback for same tag."""
    tagger.record_feedback('python', True)
    tagger.record_feedback('python', True)
    tagger.record_feedback('python', False)
    
    # 1 + 1 - 1 = 1
    assert tagger._tag_history['python'] == 1


def test_record_feedback_different_tags(tagger):
    """Test recording feedback for different tags."""
    tagger.record_feedback('python', True)
    tagger.record_feedback('java', False)
    tagger.record_feedback('cpp', True)
    
    assert tagger._tag_history['python'] == 1
    assert tagger._tag_history['java'] == -1
    assert tagger._tag_history['cpp'] == 1


# =============================================================================
# GET_TAG_STATS TESTS
# =============================================================================

def test_get_tag_stats_empty_history(tagger):
    """Test getting stats with no feedback history."""
    stats = tagger.get_tag_stats()
    
    assert stats['total_suggestions'] == 0
    assert stats['accepted_tags'] == []
    assert stats['rejected_tags'] == []
    assert stats['acceptance_rate'] == 0.0


def test_get_tag_stats_only_accepted(tagger):
    """Test stats with only accepted tags."""
    tagger.record_feedback('python', True)
    tagger.record_feedback('python', True)
    tagger.record_feedback('java', True)
    
    stats = tagger.get_tag_stats()
    
    assert stats['total_suggestions'] == 3
    assert len(stats['accepted_tags']) == 2
    assert stats['rejected_tags'] == []
    assert stats['acceptance_rate'] == 1.0


def test_get_tag_stats_only_rejected(tagger):
    """Test stats with only rejected tags."""
    tagger.record_feedback('python', False)
    tagger.record_feedback('java', False)
    
    stats = tagger.get_tag_stats()
    
    assert stats['total_suggestions'] == 2
    assert stats['accepted_tags'] == []
    assert len(stats['rejected_tags']) == 2
    assert stats['acceptance_rate'] == 0.0


def test_get_tag_stats_mixed(tagger):
    """Test stats with mixed accepted/rejected tags."""
    tagger.record_feedback('python', True)
    tagger.record_feedback('python', True)
    tagger.record_feedback('java', False)
    tagger.record_feedback('cpp', True)
    
    stats = tagger.get_tag_stats()
    
    assert stats['total_suggestions'] == 4
    assert len(stats['accepted_tags']) == 2  # python and cpp
    assert len(stats['rejected_tags']) == 1  # java
    assert stats['acceptance_rate'] == 0.75  # 3 accepts / 4 total


def test_get_tag_stats_sorted_by_count(tagger):
    """Test that stats are sorted by count descending."""
    tagger.record_feedback('python', True)
    tagger.record_feedback('python', True)
    tagger.record_feedback('python', True)
    tagger.record_feedback('java', True)
    tagger.record_feedback('cpp', True)
    tagger.record_feedback('cpp', True)
    
    stats = tagger.get_tag_stats()
    accepted = stats['accepted_tags']
    
    # Should be sorted: python(3), cpp(2), java(1)
    assert accepted[0][0] == 'python'
    assert accepted[0][1] == 3
    assert accepted[1][0] == 'cpp'
    assert accepted[1][1] == 2


def test_get_tag_stats_acceptance_rate_calculation(tagger):
    """Test acceptance rate calculation accuracy."""
    # 7 accepts, 3 rejects = 70%
    for _ in range(7):
        tagger.record_feedback('python', True)
    for _ in range(3):
        tagger.record_feedback('java', False)
    
    stats = tagger.get_tag_stats()
    
    assert stats['total_suggestions'] == 10
    assert abs(stats['acceptance_rate'] - 0.7) < 0.01


def test_get_tag_stats_net_positive_tag(tagger):
    """Test that net positive tags appear in accepted."""
    tagger.record_feedback('python', True)
    tagger.record_feedback('python', True)
    tagger.record_feedback('python', False)
    
    stats = tagger.get_tag_stats()
    
    # Net score is +1, should be in accepted
    accepted_tags = [tag for tag, _ in stats['accepted_tags']]
    assert 'python' in accepted_tags


def test_get_tag_stats_net_negative_tag(tagger):
    """Test that net negative tags appear in rejected."""
    tagger.record_feedback('java', True)
    tagger.record_feedback('java', False)
    tagger.record_feedback('java', False)
    
    stats = tagger.get_tag_stats()
    
    # Net score is -1, should be in rejected
    rejected_tags = [tag for tag, _ in stats['rejected_tags']]
    assert 'java' in rejected_tags


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_full_workflow_integration(populated_kernel):
    """Test complete workflow from initialization to tag suggestion."""
    # Create tagger
    tagger = AutoTagger(populated_kernel, min_confidence=0.4, max_suggestions=10)
    
    # Suggest tags for new content
    content = "Python machine learning tutorial with code examples"
    suggestions = await tagger.suggest_tags(content, title="ML Tutorial")
    
    # Verify suggestions
    assert len(suggestions) > 0
    assert all(s.confidence >= 0.4 for s in suggestions)
    assert len(suggestions) <= 10
    
    # Record feedback
    if suggestions:
        tagger.record_feedback(suggestions[0].tag, True)
    
    # Get stats
    stats = tagger.get_tag_stats()
    assert stats['total_suggestions'] == 1


@pytest.mark.asyncio
async def test_tag_suggestion_with_existing_tags_integration(tagger):
    """Test tag suggestion properly filters existing tags."""
    content = "Python programming with machine learning"
    existing = ['python', 'programming']
    
    suggestions = await tagger.suggest_tags(content, existing_tags=existing)
    
    # Verify no existing tags in suggestions
    suggested_tags = [s.tag for s in suggestions]
    assert 'python' not in suggested_tags
    assert 'programming' not in suggested_tags


@pytest.mark.asyncio
async def test_multiple_suggestion_rounds(tagger):
    """Test multiple rounds of suggestions."""
    contents = [
        "Python programming basics",
        "Machine learning algorithms",
        "Web development with Flask"
    ]
    
    all_suggestions = []
    for content in contents:
        suggestions = await tagger.suggest_tags(content)
        all_suggestions.extend(suggestions)
        
        # Record feedback for first suggestion
        if suggestions:
            tagger.record_feedback(suggestions[0].tag, True)
    
    # Verify feedback was recorded
    stats = tagger.get_tag_stats()
    assert stats['total_suggestions'] == len(contents)


@pytest.mark.asyncio
async def test_tag_suggestion_respects_all_constraints(populated_kernel):
    """Test that all constraints are respected simultaneously."""
    tagger = AutoTagger(populated_kernel, min_confidence=0.6, max_suggestions=3)
    
    content = "Python Python Python machine learning deep learning neural networks"
    existing = ['python']
    
    suggestions = await tagger.suggest_tags(content, existing_tags=existing)
    
    # Check all constraints
    assert len(suggestions) <= 3  # max_suggestions
    assert all(s.confidence >= 0.6 for s in suggestions)  # min_confidence
    assert 'python' not in [s.tag for s in suggestions]  # existing_tags filtered


@pytest.mark.asyncio
async def test_empty_content_returns_valid_structure(tagger):
    """Test that empty content returns valid structure."""
    suggestions = await tagger.suggest_tags("")
    
    assert isinstance(suggestions, list)
    # Even empty content might return structure-based tags


def test_tag_suggestion_object_structure(tagger):
    """Test that TagSuggestion objects have correct structure."""
    suggestions = tagger._suggest_from_frequency("python python python")
    
    for suggestion in suggestions:
        assert isinstance(suggestion, TagSuggestion)
        assert isinstance(suggestion.tag, str)
        assert isinstance(suggestion.confidence, float)
        assert isinstance(suggestion.reason, str)
        assert isinstance(suggestion.source, str)
        assert 0 <= suggestion.confidence <= 1.0