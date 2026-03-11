"""
LLM service for managing language model interactions.
"""

import os
import requests
from typing import Any

from rootcause_ai.config.providers import LLM_PROVIDERS
from rootcause_ai.utils.logging import get_logger

log = get_logger("services.llm")


def detect_models(provider: str, api_key: str | None = None) -> list[str]:
    """
    Automatically detect available models for a given provider.
    
    Args:
        provider: LLM provider name (openai, anthropic, gemini, ollama)
        api_key: API key for the provider (not needed for Ollama)
    
    Returns:
        List of available model names
    """
    log.debug(f"Detecting models for provider: {provider}")
    
    try:
        if provider == "openai" and api_key:
            return _detect_openai_models(api_key)
        
        elif provider == "anthropic" and api_key:
            return _detect_anthropic_models(api_key)
        
        elif provider == "gemini" and api_key:
            return _detect_gemini_models(api_key)
        
        elif provider == "ollama":
            return _detect_ollama_models()
    
    except Exception as e:
        log.warning(f"Error detecting models for {provider}: {e}")
    
    # Return defaults if detection fails
    log.debug(f"Using default models for {provider}")
    return LLM_PROVIDERS.get(provider, {}).get("models", [])


def _detect_openai_models(api_key: str) -> list[str]:
    """Detect available OpenAI models."""
    log.debug("Fetching OpenAI models...")
    response = requests.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10,
    )
    log.debug(f"OpenAI API response status: {response.status_code}")
    
    if response.status_code == 200:
        models = response.json().get("data", [])
        chat_models = [
            m["id"] for m in models 
            if any(x in m["id"] for x in ["gpt-4", "gpt-3.5", "o1", "o3"])
            and "instruct" not in m["id"]
        ]
        log.info(f"Found {len(chat_models)} OpenAI chat models")
        return sorted(chat_models, reverse=True)[:15] or LLM_PROVIDERS["openai"]["models"]
    
    return LLM_PROVIDERS["openai"]["models"]


def _detect_anthropic_models(api_key: str) -> list[str]:
    """Detect available Anthropic models."""
    log.debug("Fetching Anthropic models...")
    response = requests.get(
        "https://api.anthropic.com/v1/models",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        timeout=10,
    )
    log.debug(f"Anthropic API response status: {response.status_code}")
    
    if response.status_code == 200:
        models = response.json().get("data", [])
        model_ids = [m["id"] for m in models]
        log.info(f"Found {len(model_ids)} Anthropic models")
        return model_ids[:10] if model_ids else LLM_PROVIDERS["anthropic"]["models"]
    
    return LLM_PROVIDERS["anthropic"]["models"]


def _detect_gemini_models(api_key: str) -> list[str]:
    """Detect available Google Gemini models."""
    log.debug("Fetching Gemini models...")
    response = requests.get(
        f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
        timeout=10,
    )
    log.debug(f"Gemini API response status: {response.status_code}")
    
    if response.status_code == 200:
        models = response.json().get("models", [])
        gemini_models = [
            m["name"].replace("models/", "")
            for m in models
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]
        log.info(f"Found {len(gemini_models)} Gemini models")
        return gemini_models[:15] or LLM_PROVIDERS["gemini"]["models"]
    
    return LLM_PROVIDERS["gemini"]["models"]


def _detect_ollama_models() -> list[str]:
    """Detect available Ollama models."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    log.debug(f"Fetching Ollama models from {base_url}...")
    
    response = requests.get(f"{base_url}/api/tags", timeout=5)
    log.debug(f"Ollama API response status: {response.status_code}")
    
    if response.status_code == 200:
        models = response.json().get("models", [])
        model_names = [m["name"] for m in models]
        log.info(f"Found {len(model_names)} Ollama models: {model_names}")
        return model_names or LLM_PROVIDERS["ollama"]["models"]
    
    return LLM_PROVIDERS["ollama"]["models"]


def get_llm(provider: str = "openai", model: str | None = None) -> Any:
    """
    Get LangChain LLM instance based on provider.
    
    Args:
        provider: One of 'openai', 'anthropic', 'gemini', 'ollama'
        model: Specific model name (uses provider default if not specified)
    
    Returns:
        LangChain chat model instance
    """
    # Get default model if not specified
    if model is None:
        model = LLM_PROVIDERS.get(provider, {}).get("default", "gpt-4o")
    
    log.info(f"Initializing LLM: provider={provider}, model={model}")
    
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        log.debug("Creating ChatAnthropic instance")
        return ChatAnthropic(model=model, temperature=0)
    
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        log.debug("Creating ChatGoogleGenerativeAI instance")
        return ChatGoogleGenerativeAI(model=model, temperature=0)
    
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        log.debug(f"Creating ChatOllama instance with base_url={base_url}")
        return ChatOllama(model=model, base_url=base_url, temperature=0)
    
    else:  # default to openai
        from langchain_openai import ChatOpenAI
        log.debug("Creating ChatOpenAI instance")
        return ChatOpenAI(model=model, temperature=0)
