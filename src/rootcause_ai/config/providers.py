"""
LLM Provider configuration.
"""

from typing import TypedDict


class ProviderConfig(TypedDict):
    """Configuration for an LLM provider."""
    name: str
    models: list[str]
    default: str


# Supported LLM providers and their configurations
LLM_PROVIDERS: dict[str, ProviderConfig] = {
    "openai": {
        "name": "OpenAI (GPT)",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
        ],
        "default": "gpt-4o",
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "models": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ],
        "default": "claude-3-5-sonnet-20241022",
    },
    "gemini": {
        "name": "Google Gemini",
        "models": [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-pro",
        ],
        "default": "gemini-1.5-pro",
    },
    "ollama": {
        "name": "Ollama (Local)",
        "models": [
            "llama3.2",
            "llama3.1",
            "llama3",
            "mistral",
            "codellama",
            "deepseek-coder-v2",
            "qwen2.5-coder",
        ],
        "default": "llama3.2",
    },
}
