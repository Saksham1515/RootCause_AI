"""
LangGraph workflow orchestration for RootCause AI.
"""

import os

from langgraph.graph import StateGraph, END

from rootcause_ai.core.state import RootCauseState
from rootcause_ai.core.nodes import (
    scan_codebase,
    select_relevant_files,
    analyze_issue,
    generate_fix,
)
from rootcause_ai.utils.logging import get_logger

log = get_logger("core.workflow")


def build_workflow() -> StateGraph:
    """
    Build and compile the LangGraph workflow.
    
    Returns:
        Compiled workflow ready for invocation
    """
    log.debug("Building LangGraph workflow...")
    
    # Create the graph
    workflow = StateGraph(RootCauseState)
    
    # Add nodes
    workflow.add_node("scan_codebase", scan_codebase)
    workflow.add_node("select_relevant_files", select_relevant_files)
    workflow.add_node("analyze_issue", analyze_issue)
    workflow.add_node("generate_fix", generate_fix)
    
    # Define edges (sequential flow)
    workflow.set_entry_point("scan_codebase")
    workflow.add_edge("scan_codebase", "select_relevant_files")
    workflow.add_edge("select_relevant_files", "analyze_issue")
    workflow.add_edge("analyze_issue", "generate_fix")
    workflow.add_edge("generate_fix", END)
    
    log.debug("Workflow compiled successfully")
    return workflow.compile()


def run_analysis(codebase_path: str, issue_description: str) -> dict:
    """
    Run the full analysis workflow.
    
    Args:
        codebase_path: Path to the codebase to analyze
        issue_description: Description of the issue
        
    Returns:
        Final state with analysis results including:
        - root_cause: Identified root cause
        - explanation: Detailed explanation
        - suggested_fix: Suggested fix with code
        - error: Error message if any
    """
    log.info("=" * 60)
    log.info("ROOTCAUSE AI - Starting Analysis")
    log.info("=" * 60)
    log.info(f"Codebase: {codebase_path}")
    log.info(f"Issue: {issue_description[:200]}...")
    log.info(f"LLM Provider: {os.getenv('LLM_PROVIDER', 'openai')}")
    log.info(f"LLM Model: {os.getenv('LLM_MODEL', 'default')}")
    
    workflow = build_workflow()
    
    initial_state: RootCauseState = {
        "codebase_path": codebase_path,
        "issue_description": issue_description,
        "all_files": [],
        "file_summary": "",
        "relevant_files": [],
        "file_contents": {},
        "analysis": "",
        "root_cause": "",
        "explanation": "",
        "suggested_fix": "",
        "error": None,
    }
    
    log.info("Invoking workflow...")
    result = workflow.invoke(initial_state)
    
    # Log final results summary
    log.info("=" * 60)
    log.info("ANALYSIS COMPLETE - Results Summary")
    log.info("=" * 60)
    log.info(f"Files scanned: {len(result.get('all_files', []))}")
    log.info(f"Relevant files: {len(result.get('relevant_files', []))}")
    log.info(f"Root cause found: {bool(result.get('root_cause'))}")
    log.info(f"Explanation found: {bool(result.get('explanation'))}")
    log.info(f"Fix generated: {bool(result.get('suggested_fix'))}")
    log.info(f"Error: {result.get('error', 'None')}")
    
    if result.get("root_cause"):
        log.info(f"Root Cause: {result['root_cause'][:200]}...")
    else:
        log.warning("No root cause was identified!")
    
    if not result.get("suggested_fix"):
        log.warning("No fix was generated!")
    
    return result
