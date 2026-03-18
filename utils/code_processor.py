"""
Code analysis and parsing utilities
"""
import os
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CodeProcessor:
    """Process and analyze code files"""

    LANGUAGE_EXTENSIONS = {
        "python": [".py"],
        "javascript": [".js"],
        "typescript": [".ts"],
        "java": [".java"],
        "go": [".go"],
        "rust": [".rs"],
        "cpp": [".cpp", ".cc", ".cxx", ".h", ".hpp"],
        "csharp": [".cs"],
        "c": [".c", ".h"],
    }

    @staticmethod
    def detect_language(file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        for lang, extensions in CodeProcessor.LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                return lang
        return None

    @staticmethod
    def chunk_code(
        content: str, chunk_size: int = 512, overlap: int = 64
    ) -> List[Tuple[str, int, int]]:
        """
        Chunk code into overlapping segments
        Returns: [(chunk_content, start_line, end_line), ...]
        """
        lines = content.split("\n")
        total_lines = len(lines)

        chunks = []
        current_line = 0

        while current_line < total_lines:
            end_line = min(current_line + chunk_size, total_lines)
            chunk_lines = lines[current_line:end_line]
            chunk_content = "\n".join(chunk_lines)

            chunks.append((chunk_content, current_line, end_line))

            current_line = max(current_line + 1, end_line - overlap)

        return chunks

    @staticmethod
    def extract_functions(content: str, language: str) -> List[Dict]:
        """Extract function/method definitions"""
        patterns = {
            "python": r"^def\s+(\w+)\s*\(",
            "javascript": r"(?:function\s+(\w+)|const\s+(\w+)\s*=|let\s+(\w+)\s*=)",
            "typescript": r"(?:function\s+(\w+)|const\s+(\w+)\s*=|let\s+(\w+)\s*=)",
            "java": r"(?:public|private|protected)?\s+(?:static)?\s+\w+\s+(\w+)\s*\(",
            "go": r"^func\s+(?:\([^)]*\))?\s*(\w+)\s*\(",
            "rust": r"^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)",
            "cpp": r"(?:\w+::)?(\w+)\s*\(",
            "csharp": r"(?:public|private|protected)?\s+(?:static)?\s+\w+\s+(\w+)\s*\(",
        }

        pattern = patterns.get(language)
        if not pattern:
            return []

        functions = []
        for i, line in enumerate(content.split("\n"), 1):
            match = re.search(pattern, line)
            if match:
                func_name = next((g for g in match.groups() if g), None)
                if func_name:
                    functions.append(
                        {
                            "name": func_name,
                            "line": i,
                            "snippet": line.strip(),
                        }
                    )

        return functions

    @staticmethod
    def detect_imports(content: str, language: str) -> List[str]:
        """Extract imports/dependencies"""
        patterns = {
            "python": r"^(?:import|from)\s+(\S+)",
            "javascript": r"(?:import|require)\s+.*?from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\)",
            "typescript": r"(?:import|require)\s+.*?from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\)",
            "java": r"^import\s+(\S+);",
            "go": r"^import\s+[(\"]?([^)\"]+)",
            "rust": r"^use\s+(\S+);",
            "cpp": r'#include\s+[<"]([^>"]+)',
            "csharp": r"^using\s+(\S+);",
        }

        pattern = patterns.get(language)
        if not pattern:
            return []

        imports = []
        for line in content.split("\n"):
            match = re.search(pattern, line)
            if match:
                imp = next((g for g in match.groups() if g), None)
                if imp:
                    imports.append(imp)

        return imports

    @staticmethod
    def find_error_patterns(content: str, language: str) -> List[Dict]:
        """Detect common error patterns"""
        issues = []

        # Check for common issues
        error_patterns = {
            "null_pointer": {
                "python": r"(?:None\s*==|\s*==\s*None)",
                "javascript": r"(?:null|undefined)",
            },
            "unhandled_exception": {
                "python": r"(?:raise\s+\w+)",
                "javascript": r"(?:throw\s+new\s+\w+)",
            },
            "hardcoded_values": {
                "python": r'(?:path\s*=\s*["\'])/[^"\']+',
                "javascript": r'(?:const\s+\w+\s*=\s*["\'])/',
            },
        }

        for pattern_name, pattern_dict in error_patterns.items():
            if language in pattern_dict:
                pattern = pattern_dict[language]
                for i, line in enumerate(content.split("\n"), 1):
                    if re.search(pattern, line):
                        issues.append(
                            {
                                "type": pattern_name,
                                "line": i,
                                "snippet": line.strip(),
                            }
                        )

        return issues


class FileIndexer:
    """Index files in a codebase"""

    def __init__(self, max_file_size_mb: int = 1):
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.indexed_files = []

    def index_directory(self, directory: str) -> List[Dict]:
        """Recursively index all code files in directory"""
        self.indexed_files = []

        try:
            for root, dirs, files in os.walk(directory):
                # Skip common non-code directories
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "__pycache__", ".venv"]]

                for file in files:
                    file_path = os.path.join(root, file)
                    self._index_file(file_path, directory)

            logger.info(f"Indexed {len(self.indexed_files)} files")
            return self.indexed_files
        except Exception as e:
            logger.error(f"Error indexing directory: {e}")
            return []

    def _index_file(self, file_path: str, base_path: str):
        """Index a single file"""
        try:
            language = CodeProcessor.detect_language(file_path)
            if not language:
                return

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.warning(f"Skipping {file_path}: exceeds size limit")
                return

            # Read file
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Extract metadata
            relative_path = os.path.relpath(file_path, base_path)
            functions = CodeProcessor.extract_functions(content, language)
            imports = CodeProcessor.detect_imports(content, language)
            errors = CodeProcessor.find_error_patterns(content, language)

            file_info = {
                "path": relative_path,
                "language": language,
                "size": file_size,
                "lines": len(content.split("\n")),
                "functions": functions,
                "imports": imports,
                "error_patterns": errors,
                "content": content,
            }

            self.indexed_files.append(file_info)
        except Exception as e:
            logger.warning(f"Error indexing {file_path}: {e}")
