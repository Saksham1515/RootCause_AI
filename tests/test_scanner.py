"""Tests for scanner service."""

from pathlib import Path
import tempfile
import pytest

from rootcause_ai.services.scanner import (
    is_code_file,
    scan_directory,
    read_file_content,
    get_file_summary,
)


def test_is_code_file():
    """Test code file detection."""
    assert is_code_file("test.py") is True
    assert is_code_file("test.js") is True
    assert is_code_file("test.txt") is False
    assert is_code_file("test.exe") is False


def test_scan_directory():
    """Test directory scanning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        Path(tmpdir, "test.py").write_text("print('hello')")
        Path(tmpdir, "test.js").write_text("console.log('hello')")
        Path(tmpdir, "test.txt").write_text("hello")
        
        files = scan_directory(tmpdir)
        
        assert len(files) == 2  # Only .py and .js
        extensions = {f["extension"] for f in files}
        assert ".py" in extensions
        assert ".js" in extensions


def test_scan_directory_skips_ignored():
    """Test that ignored directories are skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test structure
        Path(tmpdir, "src").mkdir()
        Path(tmpdir, "src", "main.py").write_text("# main")
        Path(tmpdir, "node_modules").mkdir()
        Path(tmpdir, "node_modules", "dep.js").write_text("// dep")
        
        files = scan_directory(tmpdir)
        
        # Should only find src/main.py, not node_modules/dep.js
        assert len(files) == 1
        assert files[0]["name"] == "main.py"


def test_read_file_content():
    """Test file content reading."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("line1\nline2\nline3\n")
        f.flush()
        
        content = read_file_content(f.name)
        
        assert "line1" in content
        assert "line2" in content


def test_read_file_content_truncates():
    """Test that file content is truncated."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        # Write more than max lines
        for i in range(300):
            f.write(f"line {i}\n")
        f.flush()
        
        content = read_file_content(f.name, max_lines=10)
        
        assert "truncated" in content


def test_get_file_summary_empty():
    """Test file summary with no files."""
    summary = get_file_summary([])
    assert "No code files found" in summary


def test_get_file_summary():
    """Test file summary generation."""
    files = [
        {"relative_path": "src/main.py", "extension": ".py"},
        {"relative_path": "src/utils.py", "extension": ".py"},
        {"relative_path": "index.js", "extension": ".js"},
    ]
    
    summary = get_file_summary(files)
    
    assert "3 code files" in summary
    assert ".py files (2)" in summary
    assert ".js files (1)" in summary
