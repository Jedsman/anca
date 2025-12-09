"""
Unit tests for API schemas and validation
"""
import pytest
from pydantic import ValidationError
from app.schemas.models import GenerateRequest, JobStatusEnum


class TestGenerateRequest:
    """Test suite for GenerateRequest validation"""

    def test_valid_topic(self):
        """Test valid topic passes validation"""
        request = GenerateRequest(topic="home coffee brewing")
        assert request.topic == "home coffee brewing"

    def test_valid_topic_with_punctuation(self):
        """Test topic with allowed punctuation"""
        request = GenerateRequest(topic="Coffee: How to Brew? (Complete Guide)")
        assert "Coffee" in request.topic

    def test_topic_with_numbers(self):
        """Test topic with numbers"""
        request = GenerateRequest(topic="Top 10 Coffee Brewing Methods 2024")
        assert "2024" in request.topic

    def test_strips_whitespace(self):
        """Test leading/trailing whitespace is stripped"""
        request = GenerateRequest(topic="  home coffee brewing  ")
        assert request.topic == "home coffee brewing"

    def test_collapses_multiple_spaces(self):
        """Test multiple spaces are collapsed"""
        request = GenerateRequest(topic="home    coffee     brewing")
        assert request.topic == "home coffee brewing"

    def test_topic_too_short(self):
        """Test topic must be at least 3 characters"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(topic="ab")
        assert "at least 3 characters" in str(exc_info.value)

    def test_topic_too_long(self):
        """Test topic must be at most 200 characters"""
        long_topic = "a" * 201
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(topic=long_topic)
        assert "at most 200 characters" in str(exc_info.value)

    def test_rejects_script_injection(self):
        """Test rejection of script injection attempts"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(topic="<script>alert('xss')</script>")
        assert "suspicious content" in str(exc_info.value).lower()

    def test_rejects_javascript_protocol(self):
        """Test rejection of javascript: protocol"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(topic="javascript:void(0)")
        assert "suspicious content" in str(exc_info.value).lower()

    def test_rejects_eval_injection(self):
        """Test rejection of eval injection"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(topic="eval(malicious_code)")
        assert "suspicious content" in str(exc_info.value).lower()

    def test_rejects_system_command(self):
        """Test rejection of system command injection"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(topic="system('rm -rf /')")
        assert "suspicious content" in str(exc_info.value).lower()

    def test_rejects_python_import(self):
        """Test rejection of Python import injection"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(topic="__import__('os').system('ls')")
        assert "suspicious content" in str(exc_info.value).lower()

    def test_rejects_exec_injection(self):
        """Test rejection of exec injection"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(topic="exec('malicious')")
        assert "suspicious content" in str(exc_info.value).lower()

    def test_rejects_only_special_characters(self):
        """Test rejection of topics with only special characters"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(topic="!@#$%^&*()")
        assert "alphanumeric character" in str(exc_info.value).lower()

    def test_rejects_only_whitespace(self):
        """Test rejection of whitespace-only topics"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateRequest(topic="     ")
        assert "at least 3 characters" in str(exc_info.value).lower()

    def test_allows_common_special_chars(self):
        """Test common punctuation is allowed"""
        valid_topics = [
            "Coffee & Tea: A Comparison",
            "How-to Guide (2024)",
            "Question? Answer!",
            "Lists, Items, and More",
            "Section 1.5: Overview"
        ]
        for topic in valid_topics:
            request = GenerateRequest(topic=topic)
            assert len(request.topic) > 0


class TestJobStatusEnum:
    """Test suite for JobStatusEnum"""

    def test_all_statuses_defined(self):
        """Test all expected statuses are defined"""
        assert JobStatusEnum.PENDING == "pending"
        assert JobStatusEnum.RUNNING == "running"
        assert JobStatusEnum.COMPLETED == "completed"
        assert JobStatusEnum.FAILED == "failed"

    def test_enum_values(self):
        """Test enum can be accessed by value"""
        assert JobStatusEnum("pending") == JobStatusEnum.PENDING
        assert JobStatusEnum("running") == JobStatusEnum.RUNNING
        assert JobStatusEnum("completed") == JobStatusEnum.COMPLETED
        assert JobStatusEnum("failed") == JobStatusEnum.FAILED
