"""
Tools for agents to use during debugging
"""
import logging
from typing import List, Dict, Any, Optional
from config.schema import SearchResult, AnalysisIssue
from utils.embeddings import EmbeddingsManager
from utils.code_processor import CodeProcessor
import re

logger = logging.getLogger(__name__)


class ToolLibrary:
    """Collection of tools available to agents"""

    def __init__(self, embeddings_manager: Optional[EmbeddingsManager] = None):
        self.embeddings_manager = embeddings_manager

    # ============ FILE READING ==============
    @staticmethod
    def read_file(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        """Read file content, optionally within line range"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            if start_line is None:
                start_line = 0
            if end_line is None:
                end_line = len(lines)

            start_line = max(0, start_line - 1)  # Convert to 0-indexed
            selected_lines = lines[start_line : end_line]

            return "".join(selected_lines)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"Error reading file: {e}"

    # ============ SEMANTIC SEARCH ==============
    def semantic_search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Search for relevant code snippets using semantic similarity"""
        if not self.embeddings_manager or self.embeddings_manager.index is None:
            logger.warning("Embeddings manager not initialized")
            return []

        try:
            results = self.embeddings_manager.search(query, k=top_k)
            search_results = []

            for idx, distance in results:
                metadata = self.embeddings_manager.get_metadata(idx)
                if metadata:
                    search_results.append(
                        SearchResult(
                            file_path=metadata.get("file_path", ""),
                            chunk_index=metadata.get("chunk_index", 0),
                            content=metadata.get("content", ""),
                            relevance_score=float(1 / (1 + distance)),  # Convert distance to similarity
                            start_line=metadata.get("start_line", 0),
                            end_line=metadata.get("end_line", 0),
                        )
                    )

            return search_results
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return []

    # ============ CODE ANALYSIS ==============
    @staticmethod
    def extract_functions(file_path: str, language: str) -> List[Dict]:
        """Extract all function definitions from a file"""
        try:
            content = ToolLibrary.read_file(file_path)
            return CodeProcessor.extract_functions(content, language)
        except Exception as e:
            logger.error(f"Error extracting functions: {e}")
            return []

    @staticmethod
    def detect_imports(file_path: str, language: str) -> List[str]:
        """Extract all imports from a file"""
        try:
            content = ToolLibrary.read_file(file_path)
            return CodeProcessor.detect_imports(content, language)
        except Exception as e:
            logger.error(f"Error detecting imports: {e}")
            return []

    @staticmethod
    def find_error_patterns(file_path: str, language: str) -> List[Dict]:
        """Find common error patterns in a file"""
        try:
            content = ToolLibrary.read_file(file_path)
            return CodeProcessor.find_error_patterns(content, language)
        except Exception as e:
            logger.error(f"Error finding error patterns: {e}")
            return []

    # ============ STACK TRACE PARSING ==============
    @staticmethod
    def parse_stack_trace(stack_trace: str) -> Dict[str, Any]:
        """Parse stack trace and extract key information"""
        try:
            lines = stack_trace.strip().split("\n")

            # Find error line
            error_message = ""
            error_type = ""
            file_locations = []

            for line in lines:
                # Look for error message (usually last line)
                if "Error" in line or "Exception" in line:
                    error_message = line.strip()
                    match = re.search(r"(\w+Error|\w+Exception)", line)
                    if match:
                        error_type = match.group(1)

                # Look for file locations
                file_match = re.search(r'File "([^"]+)", line (\d+)', line)
                if file_match:
                    file_locations.append(
                        {
                            "file": file_match.group(1),
                            "line": int(file_match.group(2)),
                        }
                    )

            return {
                "error_type": error_type,
                "error_message": error_message,
                "file_locations": file_locations,
                "raw_trace": stack_trace,
            }
        except Exception as e:
            logger.error(f"Error parsing stack trace: {e}")
            return {"error": str(e)}

    # ============ DEPENDENCY MAPPING ==============
    @staticmethod
    def map_dependencies(file_path: str, language: str) -> Dict[str, List[str]]:
        """Map dependencies for a file"""
        try:
            content = ToolLibrary.read_file(file_path)
            imports = CodeProcessor.detect_imports(content, language)

            return {
                "file": file_path,
                "imports": imports,
                "language": language,
            }
        except Exception as e:
            logger.error(f"Error mapping dependencies: {e}")
            return {}

    # ============ SYNTAX CHECKING ==============
    @staticmethod
    def check_syntax(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Check for syntax errors"""
        try:
            if content is None:
                content = ToolLibrary.read_file(file_path)

            language = CodeProcessor.detect_language(file_path)
            if not language:
                return {"error": "Unknown language"}

            # Basic syntax checks (language-specific)
            issues = []

            if language == "python":
                # Check for basic Python syntax issues
                try:
                    compile(content, file_path, "exec")
                except SyntaxError as e:
                    issues.append(
                        {
                            "type": "SyntaxError",
                            "line": e.lineno,
                            "message": e.msg,
                        }
                    )

            return {
                "file": file_path,
                "language": language,
                "issues": issues,
                "is_valid": len(issues) == 0,
            }
        except Exception as e:
            logger.error(f"Error checking syntax: {e}")
            return {"error": str(e)}

    # ============ LOG ANALYSIS ==============
    @staticmethod
    def analyze_logs(log_content: str) -> Dict[str, Any]:
        """Analyze log content for error patterns"""
        try:
            lines = log_content.strip().split("\n")

            errors = []
            warnings = []
            info = []

            # Simple log level detection
            for i, line in enumerate(lines):
                if "ERROR" in line or "CRITICAL" in line:
                    errors.append({"line": i, "content": line})
                elif "WARNING" in line:
                    warnings.append({"line": i, "content": line})
                elif "INFO" in line:
                    info.append({"line": i, "content": line})

            return {
                "total_lines": len(lines),
                "error_count": len(errors),
                "warning_count": len(warnings),
                "info_count": len(info),
                "errors": errors[:10],  # First 10 errors
                "warnings": warnings[:10],  # First 10 warnings
            }
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return {"error": str(e)}

    # ============ DIFF ANALYSIS ==============
    @staticmethod
    def analyze_diff(old_content: str, new_content: str) -> Dict[str, Any]:
        """Analyze differences between two code versions"""
        try:
            old_lines = old_content.split("\n")
            new_lines = new_content.split("\n")

            changes = {
                "added_lines": [],
                "removed_lines": [],
                "modified_lines": [],
            }

            # Simple line-by-line comparison
            for i, (old_line, new_line) in enumerate(
                zip(old_lines, new_lines), 1
            ):
                if old_line != new_line:
                    changes["modified_lines"].append(
                        {"line": i, "old": old_line, "new": new_line}
                    )

            # Check for additions/deletions
            if len(new_lines) > len(old_lines):
                for i in range(len(old_lines), len(new_lines)):
                    changes["added_lines"].append(
                        {"line": i + 1, "content": new_lines[i]}
                    )
            elif len(old_lines) > len(new_lines):
                for i in range(len(new_lines), len(old_lines)):
                    changes["removed_lines"].append(
                        {"line": i + 1, "content": old_lines[i]}
                    )

            return changes
        except Exception as e:
            logger.error(f"Error analyzing diff: {e}")
            return {"error": str(e)}

    # ============ SUMMARIZATION ==============
    @staticmethod
    def summarize_content(content: str, max_length: int = 500) -> str:
        """Summarize code or text content"""
        try:
            lines = content.split("\n")
            # Return first N lines or entire content if shorter
            selected_lines = lines[:20]
            summary = "\n".join(selected_lines)

            if len(summary) > max_length:
                summary = summary[:max_length] + "..."

            return summary
        except Exception as e:
            logger.error(f"Error summarizing content: {e}")
            return ""
