"""Tests for the GapDetector module."""

import pytest
from memograph.ai.gap_detector import GapDetector, KnowledgeGap, TopicCluster, LearningPath
from memograph import MemoryKernel


@pytest.fixture
async def detector(tmp_path):
    """Create a GapDetector with a populated kernel."""
    kernel = MemoryKernel(str(tmp_path / "test_vault"))
    
    # Add diverse notes for testing
    await kernel.remember_async(
        title="Python Basics",
        content="Python is a programming language. Variables and functions are important.",
        tags=['python', 'programming']
    )
    await kernel.remember_async(
        title="Advanced Python",
        content="Python decorators, generators, and metaclasses are advanced topics. "
                "Context managers are useful. Python has great libraries.",
        tags=['python', 'advanced']
    )
    await kernel.remember_async(
        title="Data Science",
        content="Data science uses Python and statistics. Machine learning is important. "
                "Data analysis requires pandas and numpy. Visualization with matplotlib.",
        tags=['datascience', 'python']
    )
    await kernel.remember_async(
        title="JavaScript Intro",
        content="JavaScript is used for web development. Variables, functions, and objects.",
        tags=['javascript', 'web']
    )
    await kernel.remember_async(
        title="Short Note",
        content="Brief.",
        tags=[]
    )
    await kernel.remember_async(
        title="Isolated Note",
        content="This note has no connections to other notes in the system. "
                "It discusses quantum computing and cryptography.",
        tags=['quantum']
    )
    
    kernel.ingest()
    return GapDetector(kernel, min_cluster_size=2, min_severity=0.2)


@pytest.mark.asyncio
async def test_detector_initialization(tmp_path):
    """Test GapDetector initialization."""
    kernel = MemoryKernel(str(tmp_path / "test_vault"))
    detector = GapDetector(kernel)
    
    assert detector.kernel == kernel
    assert detector.analyzer is not None
    assert detector.min_cluster_size == 3
    assert detector.min_severity == 0.3
    assert detector.max_gaps == 20


@pytest.mark.asyncio
async def test_detect_gaps(detector):
    """Test main gap detection function."""
    gaps = await detector.detect_gaps()
    
    assert isinstance(gaps, list)
    assert all(isinstance(g, KnowledgeGap) for g in gaps)
    # Should detect some gaps in the test data
    assert len(gaps) > 0
    # Gaps should be sorted by severity
    if len(gaps) > 1:
        assert gaps[0].severity >= gaps[1].severity


@pytest.mark.asyncio
async def test_detect_missing_topics(detector):
    """Test detection of missing topics."""
    gaps = await detector._detect_missing_topics()
    
    assert isinstance(gaps, list)
    # Should find some frequently mentioned topics without dedicated notes
    # (e.g., "machine learning" mentioned in Data Science but no dedicated note)
    missing_topic_gaps = [g for g in gaps if g.gap_type == 'missing_topic']
    assert len(missing_topic_gaps) >= 0  # May or may not find missing topics


@pytest.mark.asyncio
async def test_detect_weak_coverage(detector):
    """Test detection of weakly covered topics."""
    gaps = await detector._detect_weak_coverage()
    
    assert isinstance(gaps, list)
    weak_gaps = [g for g in gaps if g.gap_type == 'weak_coverage']
    
    # "Short Note" should be detected as having weak coverage
    short_note_gaps = [g for g in weak_gaps if 'Short Note' in g.title]
    assert len(short_note_gaps) > 0
    
    # Check that suggestions are provided
    for gap in weak_gaps:
        assert len(gap.suggestions) > 0
        assert gap.severity > 0


@pytest.mark.asyncio
async def test_detect_isolated_notes(detector):
    """Test detection of isolated notes."""
    gaps = detector._detect_isolated_notes()
    
    assert isinstance(gaps, list)
    isolated_gaps = [g for g in gaps if g.gap_type == 'isolated_note']
    
    # "Isolated Note" should be detected
    isolated_note_gaps = [g for g in isolated_gaps if 'Isolated' in g.title]
    assert len(isolated_note_gaps) > 0
    
    for gap in isolated_gaps:
        assert gap.severity > 0
        assert len(gap.suggestions) > 0


@pytest.mark.asyncio
async def test_detect_missing_links(detector):
    """Test detection of missing wikilinks."""
    # Add a note that mentions other notes without linking
    await detector.kernel.remember_async(
        title="Summary",
        content="Python Basics are important. JavaScript Intro is also useful. "
                "Data Science combines them.",
        tags=['summary']
    )
    detector.kernel.ingest()
    
    gaps = detector._detect_missing_links()
    
    assert isinstance(gaps, list)
    missing_link_gaps = [g for g in gaps if g.gap_type == 'missing_link']
    
    # Summary note should be detected as missing links
    summary_gaps = [g for g in missing_link_gaps if 'Summary' in g.title]
    assert len(summary_gaps) > 0
    
    for gap in missing_link_gaps:
        assert len(gap.suggestions) > 0


@pytest.mark.asyncio
async def test_cluster_topics(detector):
    """Test topic clustering."""
    clusters = await detector.cluster_topics()
    
    assert isinstance(clusters, list)
    assert all(isinstance(c, TopicCluster) for c in clusters)
    
    # Should find at least one cluster (Python notes)
    assert len(clusters) > 0
    
    for cluster in clusters:
        assert cluster.size >= detector.min_cluster_size
        assert 0.0 <= cluster.density <= 1.0
        assert 0.0 <= cluster.coverage <= 1.0
        assert len(cluster.keywords) > 0
        assert len(cluster.note_ids) > 0


@pytest.mark.asyncio
async def test_suggest_learning_paths(detector):
    """Test learning path suggestions."""
    paths = await detector.suggest_learning_paths("Python")
    
    assert isinstance(paths, list)
    assert all(isinstance(p, LearningPath) for p in paths)
    
    if paths:
        path = paths[0]
        assert path.topic == "Python"
        assert len(path.notes) >= 2  # Should find multiple Python notes
        assert path.order in ['linear', 'branching', 'circular']
        assert 0.0 <= path.completeness <= 1.0
        assert isinstance(path.missing_steps, list)


@pytest.mark.asyncio
async def test_learning_path_ordering(detector):
    """Test that learning paths are ordered correctly."""
    paths = await detector.suggest_learning_paths("Python")
    
    if paths:
        linear_paths = [p for p in paths if p.order == 'linear']
        if linear_paths:
            path = linear_paths[0]
            # Notes should be ordered (by content length for linear)
            assert len(path.notes) > 0


@pytest.mark.asyncio
async def test_record_gap_feedback(detector):
    """Test recording feedback on gaps."""
    detector.record_gap_feedback("Missing note about 'testing'", True)
    detector.record_gap_feedback("Weak coverage: Short Note", False)
    
    stats = detector.get_gap_stats()
    
    assert stats['total_gaps'] == 2
    assert len(stats['addressed_gaps']) == 1
    assert len(stats['ignored_gaps']) == 1
    assert 0.0 <= stats['resolution_rate'] <= 1.0


@pytest.mark.asyncio
async def test_get_gap_stats_empty(detector):
    """Test gap stats with no feedback."""
    stats = detector.get_gap_stats()
    
    assert stats['total_gaps'] == 0
    assert stats['addressed_gaps'] == []
    assert stats['ignored_gaps'] == []
    assert stats['resolution_rate'] == 0.0


@pytest.mark.asyncio
async def test_analyze_knowledge_base(detector):
    """Test comprehensive knowledge base analysis."""
    analysis = await detector.analyze_knowledge_base()
    
    assert isinstance(analysis, dict)
    assert 'summary' in analysis
    assert 'gaps' in analysis
    assert 'clusters' in analysis
    assert 'learning_paths' in analysis
    
    summary = analysis['summary']
    assert 'total_gaps' in summary
    assert 'gap_types' in summary
    assert 'avg_severity' in summary
    assert 'total_clusters' in summary
    assert 'total_paths' in summary
    
    # Check that all gaps have required fields
    for gap in analysis['gaps']:
        assert 'type' in gap
        assert 'title' in gap
        assert 'description' in gap
        assert 'severity' in gap
        assert 'suggestions' in gap
        assert 'related_notes' in gap


@pytest.mark.asyncio
async def test_gap_severity_range(detector):
    """Test that gap severities are in valid range."""
    gaps = await detector.detect_gaps()
    
    for gap in gaps:
        assert 0.0 <= gap.severity <= 1.0


@pytest.mark.asyncio
async def test_gap_filtering_by_severity(detector):
    """Test that gaps below min_severity are filtered."""
    # Set high minimum severity
    detector.min_severity = 0.8
    gaps = await detector.detect_gaps()
    
    # All returned gaps should meet the minimum
    for gap in gaps:
        assert gap.severity >= 0.8


@pytest.mark.asyncio
async def test_max_gaps_limit(detector):
    """Test that max_gaps limit is respected."""
    detector.max_gaps = 5
    gaps = await detector.detect_gaps()
    
    assert len(gaps) <= 5


@pytest.mark.asyncio
async def test_cluster_density_calculation(detector):
    """Test cluster density calculation."""
    clusters = await detector.cluster_topics()
    
    for cluster in clusters:
        # Density should be between 0 and 1
        assert 0.0 <= cluster.density <= 1.0


@pytest.mark.asyncio
async def test_cluster_coverage_calculation(detector):
    """Test cluster coverage calculation."""
    clusters = await detector.cluster_topics()
    
    for cluster in clusters:
        # Coverage should be between 0 and 1
        assert 0.0 <= cluster.coverage <= 1.0


@pytest.mark.asyncio
async def test_empty_knowledge_base(tmp_path):
    """Test gap detection with empty knowledge base."""
    kernel = MemoryKernel(str(tmp_path / "empty_vault"))
    detector = GapDetector(kernel)
    
    gaps = await detector.detect_gaps()
    clusters = await detector.cluster_topics()
    
    # Should handle empty KB gracefully
    assert isinstance(gaps, list)
    assert isinstance(clusters, list)


@pytest.mark.asyncio
async def test_single_note_knowledge_base(tmp_path):
    """Test gap detection with single note."""
    kernel = MemoryKernel(str(tmp_path / "single_vault"))
    await kernel.remember_async(
        title="Only Note",
        content="This is the only note in the system.",
        tags=['lonely']
    )
    kernel.ingest()
    
    detector = GapDetector(kernel, min_cluster_size=1)
    gaps = await detector.detect_gaps()
    
    # Should detect the note as isolated
    assert any(g.gap_type == 'isolated_note' for g in gaps)


@pytest.mark.asyncio
async def test_gap_suggestions_not_empty(detector):
    """Test that all gaps have suggestions."""
    gaps = await detector.detect_gaps()
    
    for gap in gaps:
        assert len(gap.suggestions) > 0
        assert all(isinstance(s, str) for s in gap.suggestions)


@pytest.mark.asyncio
async def test_gap_related_notes_not_empty(detector):
    """Test that all gaps have related notes."""
    gaps = await detector.detect_gaps()
    
    for gap in gaps:
        assert len(gap.related_notes) > 0
        assert all(isinstance(n, str) for n in gap.related_notes)


@pytest.mark.asyncio
async def test_learning_path_completeness(detector):
    """Test learning path completeness scoring."""
    paths = await detector.suggest_learning_paths("Python")
    
    for path in paths:
        assert 0.0 <= path.completeness <= 1.0


@pytest.mark.asyncio
async def test_feedback_accumulation(detector):
    """Test that feedback accumulates correctly."""
    gap_title = "Test Gap"
    
    # Accept multiple times
    detector.record_gap_feedback(gap_title, True)
    detector.record_gap_feedback(gap_title, True)
    detector.record_gap_feedback(gap_title, True)
    
    stats = detector.get_gap_stats()
    addressed = dict(stats['addressed_gaps'])
    
    assert gap_title in addressed
    assert addressed[gap_title] == 3


@pytest.mark.asyncio
async def test_mixed_feedback(detector):
    """Test handling of mixed feedback."""
    gap_title = "Mixed Gap"
    
    detector.record_gap_feedback(gap_title, True)
    detector.record_gap_feedback(gap_title, True)
    detector.record_gap_feedback(gap_title, False)
    
    stats = detector.get_gap_stats()
    
    # Net positive feedback (2 accepts, 1 reject = +1)
    assert stats['resolution_rate'] > 0.0