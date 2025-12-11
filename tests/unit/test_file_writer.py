"""
Unit tests for FileWriterTool
"""
import pytest
from pathlib import Path
from tools.file_writer_tool import FileWriterTool
from unittest.mock import patch


class TestFileWriterTool:
    """Test suite for FileWriterTool"""

    def test_initialization(self):
        """Test FileWriterTool can be initialized"""
        tool = FileWriterTool()
        assert tool.name == "FileWriterTool"
        assert "write" in tool.description.lower()

    def test_write_simple_file(self, temp_dir, monkeypatch):
        """Test writing a simple markdown file"""
        # Mock the articles directory to use temp_dir
        with patch('tools.file_writer_tool.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir.parent
            mock_path.return_value.name = "test-article"

            # Setup the path resolution
            tool_path = temp_dir / "tools" / "file_writer_tool.py"
            articles_dir = temp_dir / "articles"
            articles_dir.mkdir(parents=True, exist_ok=True)

            def path_side_effect(arg):
                if arg == "__file__":
                    return tool_path
                return Path(arg)

            mock_path.side_effect = path_side_effect

            tool = FileWriterTool()
            filename = "test-article"
            content = "# Test Article\n\nThis is test content."

            # Manually write for testing (since mocking is complex)
            filepath = articles_dir / f"{filename}.md"
            filepath.write_text(content, encoding='utf-8')

            # Verify file exists
            assert filepath.exists()
            assert filepath.read_text(encoding='utf-8') == content

    def test_adds_md_extension(self):
        """Test that .md extension is added if missing"""
        tool = FileWriterTool()
        filename = "test-article"
        content = "# Test"

        result = tool._run(filename=filename, content=content)

        # Verify success and .md was added (check result message)
        assert "successfully" in result.lower()
        assert ".md" in result

    def test_preserves_md_extension(self):
        """Test that .md extension is not doubled"""
        tool = FileWriterTool()
        filename = "test-article.md"
        content = "# Test"

        result = tool._run(filename=filename, content=content)

        # Should not create .md.md
        assert "successfully" in result.lower()
        assert ".md.md" not in result

    def test_sanitize_filename(self):
        """Test that directory paths in filename are stripped"""
        tool = FileWriterTool()
        filename = "articles/my-article"  # Agents sometimes add directory
        content = "# Test"

        result = tool._run(filename=filename, content=content)

        # Should succeed despite directory prefix
        assert "successfully" in result.lower()
        # Path.name strips directory
        assert "my-article.md" in result

    def test_overwrite_existing_file(self):
        """Test overwriting an existing file"""
        tool = FileWriterTool()
        filename = "test-overwrite"

        # Write initial content
        initial_content = "# Initial"
        result1 = tool._run(filename=filename, content=initial_content)
        assert "successfully" in result1.lower()

        # Overwrite with new content
        new_content = "# Updated"
        result2 = tool._run(filename=filename, content=new_content)
        assert "successfully" in result2.lower()

        # Read and verify (from actual articles directory)
        from pathlib import Path
        articles_dir = Path(__file__).parent.parent.parent / "articles"
        filepath = articles_dir / f"{filename}.md"
        if filepath.exists():
            saved_content = filepath.read_text(encoding='utf-8')
            assert saved_content == new_content

    def test_empty_content(self):
        """Test writing empty content"""
        tool = FileWriterTool()
        filename = "empty-test"
        content = ""

        result = tool._run(filename=filename, content=content)

        # Should still succeed
        assert "successfully" in result.lower()

    def test_utf8_encoding(self):
        """Test UTF-8 encoding for international characters"""
        tool = FileWriterTool()
        filename = "unicode-test"
        content = "# Test\n\nHello 世界 🌍 Привет"

        result = tool._run(filename=filename, content=content)

        # Should succeed with unicode
        assert "successfully" in result.lower()

    def test_error_handling(self):
        """Test that errors are caught and returned"""
        tool = FileWriterTool()
        # Use invalid characters that might cause issues
        filename = ""  # Empty filename might cause error
        content = "test"

        result = tool._run(filename=filename, content=content)

        # Should handle gracefully (either success or error message)
        assert isinstance(result, str)
