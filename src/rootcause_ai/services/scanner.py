"""
Codebase scanning service.
"""

import os
from pathlib import Path

from rootcause_ai.config.settings import (
    CODE_EXTENSIONS,
    SKIP_DIRS,
    MAX_LINES_PER_FILE,
)
from rootcause_ai.utils.logging import get_logger

log = get_logger("services.scanner")


def is_code_file(file_path: str) -> bool:
    """Check if a file is a code file based on extension."""
    return Path(file_path).suffix.lower() in CODE_EXTENSIONS


def scan_directory(codebase_path: str) -> list[dict[str, str]]:
    """
    Scan a directory and return list of code files with metadata.
    
    Args:
        codebase_path: Path to the codebase to scan
    
    Returns:
        List of dicts with 'path', 'relative_path', 'name', 'extension' keys
    
    Raises:
        ValueError: If path does not exist or is not a directory
    """
    log.debug(f"Scanning directory: {codebase_path}")
    files: list[dict[str, str]] = []
    codebase = Path(codebase_path)
    
    if not codebase.exists():
        log.error(f"Path does not exist: {codebase_path}")
        raise ValueError(f"Path does not exist: {codebase_path}")
    
    if not codebase.is_dir():
        log.error(f"Path is not a directory: {codebase_path}")
        raise ValueError(f"Path is not a directory: {codebase_path}")
    
    for root, dirs, filenames in os.walk(codebase):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for filename in filenames:
            file_path = Path(root) / filename
            if is_code_file(str(file_path)):
                relative_path = file_path.relative_to(codebase)
                files.append({
                    "path": str(file_path),
                    "relative_path": str(relative_path),
                    "name": filename,
                    "extension": file_path.suffix,
                })
    
    log.debug(f"Found {len(files)} code files in {codebase_path}")
    return files


def read_file_content(file_path: str, max_lines: int = MAX_LINES_PER_FILE) -> str:
    """
    Read file content, limited to max_lines.
    
    Args:
        file_path: Path to the file
        max_lines: Maximum number of lines to read
        
    Returns:
        File content as string
    """
    log.debug(f"Reading file: {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines: list[str] = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"\n... [truncated at {max_lines} lines]")
                    break
                lines.append(line)
            
            content = "".join(lines)
            log.debug(f"Read {len(lines)} lines from {file_path}")
            return content
    
    except Exception as e:
        log.warning(f"Error reading file {file_path}: {e}")
        return f"Error reading file: {str(e)}"


def get_file_summary(files: list[dict[str, str]]) -> str:
    """
    Create a summary of scanned files for display.
    
    Args:
        files: List of file dictionaries
        
    Returns:
        Formatted summary string
    """
    if not files:
        return "No code files found in the codebase."
    
    # Group by extension
    by_extension: dict[str, list[str]] = {}
    for f in files:
        ext = f["extension"]
        if ext not in by_extension:
            by_extension[ext] = []
        by_extension[ext].append(f["relative_path"])
    
    summary_parts = [f"Found {len(files)} code files:\n"]
    
    for ext, paths in sorted(by_extension.items()):
        summary_parts.append(f"\n{ext} files ({len(paths)}):")
        for path in paths[:10]:  # Limit display
            summary_parts.append(f"  - {path}")
        if len(paths) > 10:
            summary_parts.append(f"  ... and {len(paths) - 10} more")
    
    return "\n".join(summary_parts)
