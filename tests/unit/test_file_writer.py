"""
Unit tests for FileWriterTool
"""
import pytest
from pathlib import Path
from tools.file_writer_tool import FileWriterTool


class TestFileWriterTool:
    """Test suite for FileWriterTool"""

    def test_initialization(self):
        """Test FileWriterTool can be initialized"""
        tool = FileWriterTool()
        assert tool.name == "FileWriterTool"
        assert "writes content" in tool.description.lower()

    def test_write_simple_file(self, temp_dir):
        """Test writing a simple markdown file"""
        tool = FileWriterTool()
        filename = "test-article"
        content = "# Test Article\n\nThis is test content."

        result = tool._run(
            filename=filename,
            content=content,
            output_dir=str(temp_dir)
        )

        # Verify success message
        assert "successfully" in result.lower()

        # Verify file exists
        expected_file = temp_dir / f"{filename}.md"
        assert expected_file.exists()

        # Verify content
        with open(expected_file, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        assert saved_content == content

    def test_write_with_md_extension(self, temp_dir):
        """Test writing file when .md extension is already provided"""
        tool = FileWriterTool()
        filename = "test-article.md"
        content = "# Test"

        result = tool._run(
            filename=filename,
            content=content,
            output_dir=str(temp_dir)
        )

        # Should not double the extension
        expected_file = temp_dir / "test-article.md"
        assert expected_file.exists()

        # Should not create test-article.md.md
        double_ext_file = temp_dir / "test-article.md.md"
        assert not double_ext_file.exists()

    def test_sanitize_filename(self, temp_dir):
        """Test that directory paths in filename are stripped"""
        tool = FileWriterTool()
        filename = "articles/my-article"  # Agents sometimes add directory
        content = "# Test"

        result = tool._run(
            filename=filename,
            content=content,
            output_dir=str(temp_dir)
        )

        # Should strip "articles/" prefix
        expected_file = temp_dir / "my-article.md"
        assert expected_file.exists()

    def test_overwrite_existing_file(self, temp_dir):
        """Test overwriting an existing file"""
        tool = FileWriterTool()
        filename = "test-article"

        # Write initial content
        initial_content = "# Initial"
        tool._run(filename=filename, content=initial_content, output_dir=str(temp_dir))

        # Overwrite with new content
        new_content = "# Updated"
        result = tool._run(filename=filename, content=new_content, output_dir=str(temp_dir))

        # Verify new content
        expected_file = temp_dir / f"{filename}.md"
        with open(expected_file, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        assert saved_content == new_content
        assert "initial" not in saved_content.lower()

    def test_empty_content(self, temp_dir):
        """Test writing empty content"""
        tool = FileWriterTool()
        filename = "empty"
        content = ""

        result = tool._run(filename=filename, content=content, output_dir=str(temp_dir))

        # Should still create file
        expected_file = temp_dir / "empty.md"
        assert expected_file.exists()

        with open(expected_file, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        assert saved_content == ""

    def test_utf8_encoding(self, temp_dir):
        """Test UTF-8 encoding for international characters"""
        tool = FileWriterTool()
        filename = "unicode-test"
        content = "# Test\n\nHello 世界 🌍 Привет"

        result = tool._run(filename=filename, content=content, output_dir=str(temp_dir))

        expected_file = temp_dir / "unicode-test.md"
        with open(expected_file, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        assert saved_content == content
