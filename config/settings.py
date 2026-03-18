"""
Configuration settings for RootCause AI
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Embeddings Configuration
EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDINGS_DIMENSION = 384

# FAISS Configuration
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
EMBEDDINGS_CACHE_PATH = os.getenv("EMBEDDINGS_CACHE_PATH", "./data/embeddings_cache")

# Search Configuration
SEMANTIC_SEARCH_TOP_K = int(os.getenv("SEMANTIC_SEARCH_TOP_K", "5"))
DEBUG_TRACE_DEPTH = int(os.getenv("DEBUG_TRACE_DEPTH", "10"))

# Memory Configuration
SHORT_TERM_MEMORY_SIZE = int(os.getenv("SHORT_TERM_MEMORY_SIZE", "50"))
LONG_TERM_MEMORY_PATH = os.getenv("LONG_TERM_MEMORY_PATH", "./data/long_term_memory")

# Async Configuration
MAX_CONCURRENT_AGENTS = int(os.getenv("MAX_CONCURRENT_AGENTS", "4"))
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "30"))

# Code Analysis Configuration
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "1"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))

# Supported Languages
SUPPORTED_LANGUAGES = ["python", "javascript", "typescript", "java", "go", "rust", "cpp", "csharp"]

# Graph Configuration
GRAPH_EXECUTION_TIMEOUT = int(os.getenv("GRAPH_EXECUTION_TIMEOUT", "60"))
ENABLE_VISUALIZATION = os.getenv("ENABLE_VISUALIZATION", "True").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
