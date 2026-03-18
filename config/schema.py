"""
Core data structures and state definitions for RootCause AI
"""
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime


class CodeFile(BaseModel):
    """Represents a source code file"""
    path: str
    language: str
    content: str
    size: int
    last_modified: datetime = Field(default_factory=datetime.now)
    is_chunked: bool = False
    chunks: List[str] = Field(default_factory=list)


class CodeChunk(BaseModel):
    """Represents a chunk of code and its embedding"""
    file_path: str
    chunk_index: int
    content: str
    start_line: int
    end_line: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Result from semantic search"""
    file_path: str
    chunk_index: int
    content: str
    relevance_score: float
    start_line: int
    end_line: int


class AnalysisIssue(BaseModel):
    """Detected issue during code analysis"""
    type: str  # "syntax_error", "logic_bug", "anti_pattern", "edge_case"
    severity: str  # "critical", "high", "medium", "low"
    location: str  # file:line
    description: str
    code_snippet: str
    suggested_fix: Optional[str] = None


class ExecutionState(BaseModel):
    """Shared state across all agents in the workflow"""
    # User Input
    user_query: str
    codebase_path: str
    error_logs: Optional[str] = None
    stack_trace: Optional[str] = None

    # Context
    indexed_files: List[CodeFile] = Field(default_factory=list)
    code_chunks: List[CodeChunk] = Field(default_factory=list)

    # Analysis Results
    relevant_files: List[SearchResult] = Field(default_factory=list)
    detected_issues: List[AnalysisIssue] = Field(default_factory=list)
    execution_flows: List[str] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)

    # Hypotheses
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    validated_hypotheses: List[Dict[str, Any]] = Field(default_factory=list)

    # Final Result
    root_cause: Optional[str] = None
    root_cause_confidence: float = 0.0
    affected_files: List[str] = Field(default_factory=list)
    reasoning_steps: List[str] = Field(default_factory=list)
    possible_fixes: List[str] = Field(default_factory=list)
    alternative_hypotheses: List[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    agent_logs: List[str] = Field(default_factory=list)
    execution_graph: Dict[str, Any] = Field(default_factory=dict)


class AgentMessage(BaseModel):
    """Message passed between agents"""
    agent_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    status: str  # "started", "in_progress", "completed", "failed"
    result: Optional[Any] = None
    error: Optional[str] = None


class HypothesisItem(BaseModel):
    """Represents a root cause hypothesis"""
    id: str
    description: str
    affected_components: List[str] = Field(default_factory=list)
    confidence_score: float
    reasoning: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
