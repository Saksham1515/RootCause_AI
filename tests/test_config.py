"""Tests for configuration."""

from rootcause_ai.config.providers import LLM_PROVIDERS
from rootcause_ai.config.settings import CODE_EXTENSIONS, SKIP_DIRS


def test_llm_providers_structure():
    """Test that LLM providers have required fields."""
    required_keys = {"name", "models", "default"}
    
    for provider, config in LLM_PROVIDERS.items():
        assert all(key in config for key in required_keys), f"Missing keys in {provider}"
        assert isinstance(config["models"], list)
        assert len(config["models"]) > 0
        assert config["default"] in config["models"]


def test_code_extensions():
    """Test code extensions are defined."""
    assert ".py" in CODE_EXTENSIONS
    assert ".js" in CODE_EXTENSIONS
    assert ".ts" in CODE_EXTENSIONS


def test_skip_dirs():
    """Test skip directories are defined."""
    assert "node_modules" in SKIP_DIRS
    assert "__pycache__" in SKIP_DIRS
    assert ".git" in SKIP_DIRS
