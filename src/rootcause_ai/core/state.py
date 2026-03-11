"""
State definition for the RootCause AI workflow.
"""

from typing import TypedDict


class RootCauseState(TypedDict):
    """
    State object passed through the workflow.
    
    Attributes:
        codebase_path: Path to the codebase being analyzed
        issue_description: User's description of the issue
        all_files: List of all code files found in the codebase
        file_summary: Summary of files for display
        relevant_files: List of files relevant to the issue
        file_contents: Contents of relevant files
        analysis: Raw analysis from LLM
        root_cause: Identified root cause
        explanation: Detailed explanation of the root cause
        suggested_fix: Suggested fix with code examples
        error: Error message if any step failed
    """
    codebase_path: str
    issue_description: str
    all_files: list[dict]
    file_summary: str
    relevant_files: list[str]
    file_contents: dict[str, str]
    analysis: str
    root_cause: str
    explanation: str
    suggested_fix: str
    error: str | None
