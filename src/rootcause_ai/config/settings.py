"""
Application settings and constants.
"""

from pathlib import Path

# =============================================================================
# File Scanning Configuration
# =============================================================================

# File extensions to scan (code files)
CODE_EXTENSIONS: set[str] = {
    # Python
    ".py",
    # JavaScript/TypeScript
    ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
    # Web
    ".html", ".css", ".scss", ".sass", ".less", ".vue", ".svelte",
    # JVM
    ".java", ".kt", ".scala", ".groovy",
    # Systems
    ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".cs",
    # Scripting
    ".rb", ".php", ".swift", ".pl", ".lua",
    # Data/Config
    ".sql", ".yaml", ".yml", ".json", ".xml", ".toml",
    # Documentation
    ".md", ".rst",
}

# Directories to skip during scanning
SKIP_DIRS: set[str] = {
    # Version control
    ".git", ".svn", ".hg",
    # Dependencies
    "node_modules", "vendor", "bower_components",
    # Python
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "venv", ".venv", "env", ".env", "virtualenv",
    "*.egg-info", "dist", "build", "eggs", ".eggs",
    # IDE/Editor
    ".idea", ".vscode", ".vs",
    # Build outputs
    "target", "bin", "obj", "out", "output",
    ".next", ".nuxt", ".output",
    # Test/Coverage
    "coverage", "htmlcov", ".coverage",
    # Misc
    ".tox", ".nox", ".cache",
}

# =============================================================================
# Processing Limits
# =============================================================================

# Maximum lines to read per file (to control token usage)
MAX_LINES_PER_FILE: int = 200

# Maximum number of relevant files to select
MAX_RELEVANT_FILES: int = 10

# =============================================================================
# Paths
# =============================================================================

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Logs directory
LOGS_DIR = PROJECT_ROOT / "logs"
