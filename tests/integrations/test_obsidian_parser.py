"""Tests for Obsidian markdown parser."""

import tempfile
from pathlib import Path

import pytest

from memograph.integrations.obsidian.parser import ObsidianParser


@pytest.fixture
def parser():
    """Create parser instance."""
    return ObsidianParser()


@pytest.fixture
def sample_note_path():
    """Get path to sample note fixture."""
    return Path(__file__).parent.parent / "fixtures" / "obsidian" / "sample_note.md"


class TestObsidianParser:
    """Test ObsidianParser class."""

    def test_parse_file_with_frontmatter(self, parser, sample_note_path):
        """Test parsing file with frontmatter."""
        result = parser.parse_file(sample_note_path)

        # Check basic structure
        assert "title" in result
        assert "content" in result
        assert "tags" in result
        assert "metadata" in result
        assert "wikilinks" in result
        assert "backlinks" in result
        assert "path" in result
        assert "modified" in result

        # Check frontmatter extraction
        assert result["title"] == "Test Note"
        assert result["tags"] == ["test", "sample"]
        # python-frontmatter parses dates automatically
        import datetime

        assert result["metadata"]["created"] == datetime.date(2024, 1, 1)
        assert result["metadata"]["author"] == "Test Author"

        # Check content is extracted (without frontmatter)
        assert "This is a test note" in result["content"]
        assert (
            "---" not in result["content"]
        )  # Frontmatter delimiters should be removed

        # Check path
        assert str(sample_note_path) == result["path"]

        # Check modified timestamp exists
        assert isinstance(result["modified"], float)
        assert result["modified"] > 0

        # Check backlinks is empty list
        assert result["backlinks"] == []

    def test_parse_file_without_frontmatter(self, parser):
        """Test parsing file without frontmatter."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("# Simple Note\n\nThis is content without frontmatter.")
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)

            # Should use filename as title
            assert result["title"] == temp_path.stem

            # Should have empty tags
            assert result["tags"] == []

            # Should have empty metadata
            assert result["metadata"] == {}

            # Content should be present
            assert "Simple Note" in result["content"]

        finally:
            temp_path.unlink()

    def test_parse_file_empty_file(self, parser):
        """Test parsing empty file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)

            # Should handle empty file gracefully
            assert result["title"] == temp_path.stem
            assert result["content"] == ""
            assert result["tags"] == []
            assert result["wikilinks"] == []

        finally:
            temp_path.unlink()

    def test_extract_wikilinks(self, parser, sample_note_path):
        """Test extracting wikilinks from content."""
        result = parser.parse_file(sample_note_path)
        wikilinks = result["wikilinks"]

        # Check all wikilinks are found
        assert "wikilink" in wikilinks
        assert "another link" in wikilinks
        assert "yet another link" in wikilinks
        assert "Documentation" in wikilinks
        assert "API Reference" in wikilinks

        # Check count
        assert len(wikilinks) == 5

    def test_extract_wikilinks_with_special_characters(self, parser):
        """Test extracting wikilinks with special characters."""
        content = "Link to [[My Page-Name]] and [[Page_With_Underscores]]"
        wikilinks = parser.extract_wikilinks(content)

        assert "My Page-Name" in wikilinks
        assert "Page_With_Underscores" in wikilinks
        assert len(wikilinks) == 2

    def test_extract_wikilinks_no_links(self, parser):
        """Test extracting wikilinks when none exist."""
        content = "This is content without any links."
        wikilinks = parser.extract_wikilinks(content)

        assert wikilinks == []

    def test_extract_tags(self, parser):
        """Test extracting tags from content."""
        content = "This has #tag1 and #tag2 and #another_tag"
        tags = parser.extract_tags(content)

        assert "tag1" in tags
        assert "tag2" in tags
        assert "another_tag" in tags
        assert len(tags) == 3

    def test_extract_tags_from_sample_note(self, parser, sample_note_path):
        """Test extracting tags from sample note."""
        result = parser.parse_file(sample_note_path)

        # Extract tags from content
        content_tags = parser.extract_tags(result["content"])

        # Check content tags
        assert "hashtag" in content_tags
        assert "tag1" in content_tags
        assert "tag2" in content_tags
        assert "project" in content_tags
        assert "memograph" in content_tags

    def test_extract_tags_no_tags(self, parser):
        """Test extracting tags when none exist."""
        content = "This is content without any tags."
        tags = parser.extract_tags(content)

        assert tags == []

    def test_extract_tags_with_numbers(self, parser):
        """Test extracting tags with numbers."""
        content = "Tags like #tag123 and #2024"
        tags = parser.extract_tags(content)

        assert "tag123" in tags
        assert "2024" in tags

    def test_parse_file_with_partial_frontmatter(self, parser):
        """Test parsing file with only some frontmatter fields."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("""---
title: Partial Note
---

Content here.
""")
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)

            # Should extract title
            assert result["title"] == "Partial Note"

            # Should have empty tags (not in frontmatter)
            assert result["tags"] == []

            # Metadata should only have title
            assert "title" in result["metadata"]
            assert len(result["metadata"]) == 1

        finally:
            temp_path.unlink()

    def test_parse_file_with_unicode_content(self, parser):
        """Test parsing file with unicode characters."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("""---
title: Unicode Test
---

This has unicode: 你好世界 🌍 [[Link with émojis]]
#unicode #日本語
""")
            temp_path = Path(f.name)

        try:
            result = parser.parse_file(temp_path)

            # Should handle unicode in content
            assert "你好世界" in result["content"]
            assert "🌍" in result["content"]

            # Should extract wikilinks with unicode
            assert "Link with émojis" in result["wikilinks"]

        finally:
            temp_path.unlink()

    def test_wikilinks_nested_brackets(self, parser):
        """Test that nested brackets don't break wikilink extraction."""
        content = "[[normal link]] and some [[link|with pipes]]"
        wikilinks = parser.extract_wikilinks(content)

        # Should extract both
        assert "normal link" in wikilinks
        assert "link|with pipes" in wikilinks

    def test_multiple_tags_on_same_line(self, parser):
        """Test extracting multiple tags on same line."""
        content = "#tag1 #tag2 #tag3"
        tags = parser.extract_tags(content)

        assert len(tags) == 3
        assert all(f"tag{i}" in tags for i in [1, 2, 3])
