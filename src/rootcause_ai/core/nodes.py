"""
Workflow nodes for RootCause AI.

Each node is a function that takes a RootCauseState and returns an updated state.
"""

import json
import os
import re
import traceback

from langchain_core.messages import HumanMessage, SystemMessage

from rootcause_ai.core.state import RootCauseState
from rootcause_ai.services.llm import get_llm
from rootcause_ai.services.scanner import (
    scan_directory,
    read_file_content,
    get_file_summary,
)
from rootcause_ai.utils.logging import get_logger

log = get_logger("core.nodes")


def scan_codebase(state: RootCauseState) -> RootCauseState:
    """
    Node 1: Scan the codebase and collect all code files.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with all_files and file_summary
    """
    log.info("=" * 50)
    log.info("NODE 1: scan_codebase - Starting")
    log.info(f"Codebase path: {state['codebase_path']}")
    log.info(f"Issue: {state['issue_description'][:100]}...")
    
    try:
        codebase_path = state["codebase_path"]
        files = scan_directory(codebase_path)
        file_summary = get_file_summary(files)
        
        log.info(f"Scan complete: Found {len(files)} code files")
        log.debug(f"File types: {set(f['extension'] for f in files)}")
        
        return {
            **state,
            "all_files": files,
            "file_summary": file_summary,
            "error": None,
        }
    except Exception as e:
        log.error(f"Error in scan_codebase: {e}")
        log.debug(traceback.format_exc())
        return {
            **state,
            "all_files": [],
            "file_summary": "",
            "error": f"Error scanning codebase: {str(e)}",
        }


def select_relevant_files(state: RootCauseState) -> RootCauseState:
    """
    Node 2: Use LLM to select relevant files based on the issue.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with relevant_files and file_contents
    """
    log.info("=" * 50)
    log.info("NODE 2: select_relevant_files - Starting")
    
    if state.get("error"):
        log.warning(f"Skipping due to previous error: {state['error']}")
        return state
    
    log.info(f"Total files to analyze: {len(state['all_files'])}")
    
    try:
        llm = get_llm(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL"),
        )
        
        # Build file list for LLM
        file_list = "\n".join([f["relative_path"] for f in state["all_files"]])
        log.debug(f"File list for LLM:\n{file_list[:500]}...")
        
        system_prompt = """You are a senior software engineer analyzing a codebase.
Given an issue description and a list of files, select the most relevant files that are likely related to the issue.
Return ONLY a JSON array of file paths, nothing else.
Select at most 10 most relevant files.
Example response: ["src/api/checkout.py", "src/models/order.py"]"""

        user_prompt = f"""Issue: {state["issue_description"]}

Available files:
{file_list}

Select the most relevant files that could be related to this issue.
Return only a JSON array of relative file paths."""

        log.info("Invoking LLM to select relevant files...")
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        
        log.debug(f"LLM response received: {len(response.content)} chars")
        log.debug(f"Raw LLM response: {response.content[:500]}")
        
        # Parse response - extract JSON array
        response_text = response.content
        json_match = re.search(r"\[.*?\]", response_text, re.DOTALL)
        
        if json_match:
            relevant_paths = json.loads(json_match.group())
            log.info(f"Parsed {len(relevant_paths)} relevant file paths from LLM response")
        else:
            relevant_paths = []
            log.warning(f"Could not parse JSON array from response: {response_text[:200]}")
        
        # Map relative paths to full paths
        path_map = {f["relative_path"]: f["path"] for f in state["all_files"]}
        relevant_files = [path_map[p] for p in relevant_paths if p in path_map]
        log.info(f"Mapped to {len(relevant_files)} full file paths")
        
        # Read file contents
        file_contents: dict[str, str] = {}
        for file_path in relevant_files:
            log.debug(f"Reading file: {file_path}")
            content = read_file_content(file_path)
            rel_path = next(
                (f["relative_path"] for f in state["all_files"] if f["path"] == file_path),
                file_path,
            )
            file_contents[rel_path] = content
            log.debug(f"Read {len(content)} chars from {rel_path}")
        
        log.info(f"NODE 2 complete: Read {len(file_contents)} files")
        
        return {
            **state,
            "relevant_files": relevant_files,
            "file_contents": file_contents,
            "error": None,
        }
    except Exception as e:
        log.error(f"Error in select_relevant_files: {e}")
        log.debug(traceback.format_exc())
        return {
            **state,
            "relevant_files": [],
            "file_contents": {},
            "error": f"Error selecting relevant files: {str(e)}",
        }


def analyze_issue(state: RootCauseState) -> RootCauseState:
    """
    Node 3: Analyze the code and identify root cause.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with analysis, root_cause, and explanation
    """
    log.info("=" * 50)
    log.info("NODE 3: analyze_issue - Starting")
    
    if state.get("error"):
        log.warning(f"Skipping due to previous error: {state['error']}")
        return state
    
    if not state.get("file_contents"):
        log.warning("No file contents available for analysis")
        return {
            **state,
            "analysis": "",
            "root_cause": "Could not identify relevant files for analysis.",
            "explanation": "No relevant files were found in the codebase for this issue.",
            "error": None,
        }
    
    log.info(f"Analyzing {len(state.get('file_contents', {}))} files")
    
    try:
        llm = get_llm(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL"),
        )
        
        # Build code context
        code_context = ""
        for path, content in state["file_contents"].items():
            code_context += f"\n\n=== {path} ===\n{content}"
        
        log.debug(f"Code context size: {len(code_context)} chars")
        
        system_prompt = """You are a senior software engineer debugging an issue.
Analyze the provided code carefully and identify the root cause of the reported issue.
Be specific and reference actual code when possible.
Structure your response as:

ROOT CAUSE:
[One clear sentence identifying the root cause]

EXPLANATION:
[Detailed explanation of why this is happening, referencing specific code]"""

        user_prompt = f"""Issue reported: {state["issue_description"]}

Code from relevant files:
{code_context}

Analyze this code and identify the root cause of the issue."""

        log.info("Invoking LLM for root cause analysis...")
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        
        analysis = response.content
        log.debug(f"Analysis response received: {len(analysis)} chars")
        log.debug(f"Raw analysis response: {analysis[:500]}...")
        
        # Parse root cause and explanation
        root_cause = ""
        explanation = ""
        
        if "ROOT CAUSE:" in analysis:
            log.debug("Parsing ROOT CAUSE and EXPLANATION from response")
            parts = analysis.split("ROOT CAUSE:")
            if len(parts) > 1:
                rest = parts[1]
                if "EXPLANATION:" in rest:
                    root_cause = rest.split("EXPLANATION:")[0].strip()
                    explanation = rest.split("EXPLANATION:")[1].strip()
                else:
                    root_cause = rest.strip()
        else:
            log.warning("Response does not contain 'ROOT CAUSE:' marker, using full response")
            root_cause = analysis
        
        log.info(f"NODE 3 complete: root_cause={len(root_cause)} chars, explanation={len(explanation)} chars")
        log.info(f"Root cause preview: {root_cause[:150]}...")
        
        return {
            **state,
            "analysis": analysis,
            "root_cause": root_cause,
            "explanation": explanation,
            "error": None,
        }
    except Exception as e:
        log.error(f"Error in analyze_issue: {e}")
        log.debug(traceback.format_exc())
        return {
            **state,
            "analysis": "",
            "root_cause": "",
            "explanation": "",
            "error": f"Error analyzing issue: {str(e)}",
        }


def generate_fix(state: RootCauseState) -> RootCauseState:
    """
    Node 4: Generate fix suggestions.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with suggested_fix
    """
    log.info("=" * 50)
    log.info("NODE 4: generate_fix - Starting")
    
    if state.get("error"):
        log.warning(f"Skipping due to previous error: {state['error']}")
        return state
    
    if not state.get("root_cause"):
        log.warning("No root cause available, cannot generate fix")
        return {
            **state,
            "suggested_fix": "Unable to generate fix without root cause analysis.",
        }
    
    log.info(f"Generating fix based on root cause: {state['root_cause'][:100]}...")
    
    try:
        llm = get_llm(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL"),
        )
        
        # Build code context
        code_context = ""
        for path, content in state.get("file_contents", {}).items():
            code_context += f"\n\n=== {path} ===\n{content}"
        
        system_prompt = """You are a senior software engineer providing a fix for a bug.
Based on the root cause analysis, suggest a specific fix with code examples.
Keep suggestions practical and actionable.
Include code snippets showing the suggested changes."""

        user_prompt = f"""Issue: {state["issue_description"]}

Root Cause: {state["root_cause"]}

Explanation: {state["explanation"]}

Relevant Code:
{code_context}

Suggest a fix for this issue with specific code changes."""

        log.info("Invoking LLM for fix suggestions...")
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        
        log.info(f"NODE 4 complete: Generated fix with {len(response.content)} chars")
        log.debug(f"Fix preview: {response.content[:300]}...")
        
        return {
            **state,
            "suggested_fix": response.content,
            "error": None,
        }
    except Exception as e:
        log.error(f"Error in generate_fix: {e}")
        log.debug(traceback.format_exc())
        return {
            **state,
            "suggested_fix": "",
            "error": f"Error generating fix: {str(e)}",
        }
