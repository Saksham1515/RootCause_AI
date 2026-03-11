# RootCause AI

An AI-powered debugging assistant that analyzes local codebases and explains the root cause of issues.

## Features

- **Codebase Scanner**: Automatically scans your project for relevant code files
- **Smart File Selection**: Uses LLM to identify files most relevant to your issue
- **Root Cause Analysis**: Analyzes code to identify the probable root cause
- **Fix Suggestions**: Provides actionable suggestions with code examples
- **Multi-Provider Support**: Works with OpenAI, Anthropic, Google Gemini, and Ollama

## Architecture

```
User Input
    |
+-------------------------------------+
|         LangGraph Workflow          |
+-------------------------------------+
|  Node 1: Codebase Scanner           |
|  Node 2: Relevant File Selector     |
|  Node 3: Root Cause Analyzer        |
|  Node 4: Fix Generator              |
+-------------------------------------+
    |
Root Cause + Explanation + Fix
```

## Tech Stack

- **Python 3.10+**
- **LangGraph** - Workflow orchestration
- **LangChain** - LLM integration
- **Streamlit** - Web UI
- **LLM Providers:**
  - OpenAI (GPT-4o, GPT-4, GPT-3.5)
  - Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
  - Google Gemini (Gemini 1.5 Pro, Gemini Flash)
  - Ollama (Llama 3, Mistral, CodeLlama, local models)

## Installation

### Using uv (Recommended)

```bash
# Install uv if you haven't
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to project and sync dependencies
cd RootCause_AI
uv sync
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install package
pip install -e .
```

## Configuration

Set up environment variables (optional - can also enter in UI):

```bash
# Create .env file
cp .env.example .env

# Add your API keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
```

## Usage

### Streamlit UI (Recommended)

```bash
# With uv
uv run python run.py

# Or directly with streamlit
uv run streamlit run src/rootcause_ai/ui/app.py
```

Then open http://localhost:8501 in your browser.

### Command Line

```bash
# With uv
uv run rootcause "/path/to/codebase" "Description of the issue"

# With options
uv run rootcause "/path/to/codebase" "Issue" --provider anthropic
```

### As a Library

```python
from rootcause_ai import run_analysis

result = run_analysis(
    codebase_path="/path/to/your/codebase",
    issue_description="Checkout API returns 500 error"
)

print(f"Root Cause: {result['root_cause']}")
print(f"Suggested Fix: {result['suggested_fix']}")
```

## Project Structure

```
RootCause_AI/
+-- src/
|   +-- rootcause_ai/
|       +-- __init__.py           # Package exports
|       +-- cli.py                # Command-line interface
|       +-- config/
|       |   +-- settings.py       # Constants
|       |   +-- providers.py      # LLM provider configs
|       +-- core/
|       |   +-- state.py          # Workflow state
|       |   +-- nodes.py          # Workflow nodes
|       |   +-- workflow.py       # LangGraph orchestration
|       +-- services/
|       |   +-- llm.py            # LLM service
|       |   +-- scanner.py        # Codebase scanner
|       +-- utils/
|       |   +-- logging.py        # Logging configuration
|       +-- ui/
|           +-- app.py            # Streamlit application
|           +-- components.py     # UI components
+-- tests/
+-- logs/
+-- run.py                        # Quick start script
+-- pyproject.toml
+-- README.md
```

## Logging

Logs are written to both console (INFO+) and file (DEBUG+) at `logs/rootcause_YYYYMMDD.log`.

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```

## License

MIT
