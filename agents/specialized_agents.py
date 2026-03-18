"""
Specialized agents for RootCause AI
"""
import logging
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from config.schema import ExecutionState, AgentMessage, HypothesisItem
from tools.tool_library import ToolLibrary
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all agents"""

    def __init__(self, name: str, role: str, llm_model: str = "gpt-4"):
        self.name = name
        self.role = role
        self.llm = ChatOpenAI(model=llm_model, temperature=0.7)
        self.tool_library = ToolLibrary()

    def _log_action(self, action: str, details: Dict = None) -> AgentMessage:
        """Log agent action"""
        return AgentMessage(
            agent_name=self.name,
            action=action,
            details=details or {},
            status="started",
        )

    def _complete_action(self, message: AgentMessage, result: Any):
        """Mark action as complete"""
        message.status = "completed"
        message.result = result
        message.timestamp = datetime.now()

    def _fail_action(self, message: AgentMessage, error: str):
        """Mark action as failed"""
        message.status = "failed"
        message.error = error
        message.timestamp = datetime.now()


class PlannerAgent(BaseAgent):
    """Breaks down user query into structured execution plan"""

    def __init__(self):
        super().__init__(
            name="Planner",
            role="Plan complex debugging tasks into manageable sub-tasks",
        )

    def plan(self, state: ExecutionState) -> Dict[str, Any]:
        """Generate execution plan"""
        message = self._log_action("plan_generation", {"query": state.user_query})

        try:
            prompt = f"""
You are an expert debugging coordinator. Analyze this issue and create a detailed execution plan.

User Query: {state.user_query}
Has Error Logs: {state.error_logs is not None}
Has Stack Trace: {state.stack_trace is not None}

Generate a JSON plan with:
1. priority_analysis_steps: What to analyze first
2. required_agents: Which agents to invoke and in what order
3. parallel_opportunities: Which tasks can run in parallel
4. conditional_paths: If X then do Y
5. estimated_effort: Time complexity

Return ONLY valid JSON, no markdown.
"""

            response = self.llm.invoke(prompt)
            plan_text = response.content.strip()

            # Parse JSON response
            if "```json" in plan_text:
                plan_text = plan_text.split("```json")[1].split("```")[0]
            elif "```" in plan_text:
                plan_text = plan_text.split("```")[1].split("```")[0]

            plan = json.loads(plan_text)
            self._complete_action(message, plan)

            return {
                "success": True,
                "plan": plan,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            self._fail_action(message, str(e))
            return {
                "success": False,
                "error": str(e),
                "message": message,
            }


class ContextBuilderAgent(BaseAgent):
    """Scans and indexes codebase"""

    def __init__(self):
        super().__init__(
            name="ContextBuilder",
            role="Build comprehensive index of codebase structure",
        )

    def build_context(self, state: ExecutionState) -> Dict[str, Any]:
        """Build context from codebase"""
        message = self._log_action("context_building", {"codebase": state.codebase_path})

        try:
            from utils.code_processor import FileIndexer

            indexer = FileIndexer()
            indexed_files = indexer.index_directory(state.codebase_path)

            # Build summary
            summary = {
                "total_files": len(indexed_files),
                "by_language": {},
                "total_lines": 0,
                "functions_found": 0,
            }

            for file_info in indexed_files:
                lang = file_info["language"]
                summary["by_language"][lang] = summary["by_language"].get(lang, 0) + 1
                summary["total_lines"] += file_info["lines"]
                summary["functions_found"] += len(file_info["functions"])

            self._complete_action(message, summary)

            return {
                "success": True,
                "indexed_files": indexed_files,
                "summary": summary,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Context building failed: {e}")
            self._fail_action(message, str(e))
            return {
                "success": False,
                "error": str(e),
                "message": message,
            }


class RetrieverAgent(BaseAgent):
    """Performs semantic search on codebase"""

    def __init__(self):
        super().__init__(
            name="Retriever",
            role="Find relevant code through semantic search",
        )

    def retrieve(self, state: ExecutionState, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve relevant code snippets"""
        message = self._log_action("semantic_search", {"query": query, "top_k": top_k})

        try:
            results = self.tool_library.semantic_search(query, top_k=top_k)

            self._complete_action(message, {"results_count": len(results)})

            return {
                "success": True,
                "results": results,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            self._fail_action(message, str(e))
            return {
                "success": False,
                "error": str(e),
                "message": message,
            }


class CodeReasoningAgent(BaseAgent):
    """Understands code logic and traces execution flows"""

    def __init__(self):
        super().__init__(
            name="CodeReasoner",
            role="Analyze code logic and execution flows",
        )

    def analyze_code(self, state: ExecutionState, files: List[str]) -> Dict[str, Any]:
        """Analyze code logic"""
        message = self._log_action("code_analysis", {"files": files})

        try:
            analysis = {
                "functions": [],
                "imports": [],
                "call_chains": [],
            }

            for file_path in files:
                language = "python"  # Assume for now
                funcs = self.tool_library.extract_functions(file_path, language)
                imports = self.tool_library.detect_imports(file_path, language)

                analysis["functions"].extend(funcs)
                analysis["imports"].extend(imports)

            self._complete_action(message, {"items_analyzed": len(files)})

            return {
                "success": True,
                "analysis": analysis,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            self._fail_action(message, str(e))
            return {
                "success": False,
                "error": str(e),
                "message": message,
            }


class BugDetectionAgent(BaseAgent):
    """Detects syntax issues, logical bugs, and anti-patterns"""

    def __init__(self):
        super().__init__(
            name="BugDetector",
            role="Identify bugs and anti-patterns in code",
        )

    def detect_bugs(self, state: ExecutionState, files: List[str]) -> Dict[str, Any]:
        """Detect bugs in code"""
        message = self._log_action("bug_detection", {"files": files})

        try:
            issues = []

            for file_path in files:
                language = "python"

                # Check syntax
                syntax_check = self.tool_library.check_syntax(file_path)
                issues.extend(syntax_check.get("issues", []))

                # Find error patterns
                patterns = self.tool_library.find_error_patterns(file_path, language)
                issues.extend(patterns)

            self._complete_action(message, {"issues_found": len(issues)})

            return {
                "success": True,
                "issues": issues,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Bug detection failed: {e}")
            self._fail_action(message, str(e))
            return {
                "success": False,
                "error": str(e),
                "message": message,
            }


class LogAnalysisAgent(BaseAgent):
    """Analyzes logs and stack traces"""

    def __init__(self):
        super().__init__(
            name="LogAnalyzer",
            role="Parse and analyze logs and stack traces",
        )

    def analyze_logs(self, state: ExecutionState) -> Dict[str, Any]:
        """Analyze logs"""
        message = self._log_action("log_analysis", {"has_logs": state.error_logs is not None})

        try:
            analysis = {}

            if state.error_logs:
                log_analysis = self.tool_library.analyze_logs(state.error_logs)
                analysis["logs"] = log_analysis

            if state.stack_trace:
                trace_analysis = self.tool_library.parse_stack_trace(state.stack_trace)
                analysis["trace"] = trace_analysis

            self._complete_action(message, {"analysis_items": len(analysis)})

            return {
                "success": True,
                "analysis": analysis,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Log analysis failed: {e}")
            self._fail_action(message, str(e))
            return {
                "success": False,
                "error": str(e),
                "message": message,
            }


class DependencyTrackerAgent(BaseAgent):
    """Tracks dependencies across modules"""

    def __init__(self):
        super().__init__(
            name="DependencyTracker",
            role="Map and track dependencies across codebase",
        )

    def track_dependencies(self, state: ExecutionState, files: List[str]) -> Dict[str, Any]:
        """Track dependencies"""
        message = self._log_action("dependency_tracking", {"files": files})

        try:
            dependency_map = {}

            for file_path in files:
                language = "python"
                deps = self.tool_library.map_dependencies(file_path, language)
                dependency_map[file_path] = deps

            self._complete_action(message, {"files_analyzed": len(files)})

            return {
                "success": True,
                "dependencies": dependency_map,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Dependency tracking failed: {e}")
            self._fail_action(message, str(e))
            return {
                "success": False,
                "error": str(e),
                "message": message,
            }


class HypothesisAgent(BaseAgent):
    """Generates multiple possible root cause hypotheses"""

    def __init__(self):
        super().__init__(
            name="Hypothesis",
            role="Generate and rank root cause hypotheses",
        )

    def generate_hypotheses(self, state: ExecutionState) -> Dict[str, Any]:
        """Generate hypotheses"""
        message = self._log_action("hypothesis_generation", {})

        try:
            # Summarize findings
            findings = {
                "issues_count": len(state.detected_issues),
                "error_type": state.stack_trace[:100] if state.stack_trace else "Unknown",
                "relevant_files": len(state.relevant_files),
            }

            prompt = f"""
Based on these debugging findings, generate 3-5 plausible root cause hypotheses:

{json.dumps(findings, indent=2)}

For each hypothesis, provide:
- description: Clear explanation
- confidence: 0.0-1.0
- affected_components: List of involved files/modules
- reasoning: Why this could be the root cause

Return ONLY valid JSON array, no markdown.
"""

            response = self.llm.invoke(prompt)
            hypotheses_text = response.content.strip()

            if "```json" in hypotheses_text:
                hypotheses_text = hypotheses_text.split("```json")[1].split("```")[0]
            elif "```" in hypotheses_text:
                hypotheses_text = hypotheses_text.split("```")[1].split("```")[0]

            hypotheses = json.loads(hypotheses_text)

            # Convert to HypothesisItem objects
            hypothesis_items = []
            for i, hyp in enumerate(hypotheses):
                hypothesis_items.append(
                    HypothesisItem(
                        id=f"hyp_{i}",
                        description=hyp.get("description", ""),
                        affected_components=hyp.get("affected_components", []),
                        confidence_score=hyp.get("confidence", 0.0),
                        reasoning=hyp.get("reasoning", []),
                    )
                )

            self._complete_action(message, {"hypotheses_count": len(hypothesis_items)})

            return {
                "success": True,
                "hypotheses": hypothesis_items,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Hypothesis generation failed: {e}")
            self._fail_action(message, str(e))
            return {
                "success": False,
                "error": str(e),
                "message": message,
            }


class CriticAgent(BaseAgent):
    """Validates and refines hypotheses"""

    def __init__(self):
        super().__init__(
            name="Critic",
            role="Validate hypotheses and refine reasoning",
        )

    def critique(self, state: ExecutionState) -> Dict[str, Any]:
        """Critique and validate hypotheses"""
        message = self._log_action("hypothesis_critique", {})

        try:
            validated = []

            for hyp in state.hypotheses:
                # Simple validation logic
                score = hyp.get("confidence_score", 0)

                # Increase confidence if well-supported
                supporting_evidence = hyp.get("supporting_evidence", [])
                if len(supporting_evidence) > 0:
                    score = min(1.0, score + 0.1 * len(supporting_evidence))

                validated.append({**hyp, "refined_confidence": score})

            # Sort by confidence
            validated.sort(key=lambda x: x["refined_confidence"], reverse=True)

            self._complete_action(message, {"hypotheses_validated": len(validated)})

            return {
                "success": True,
                "validated_hypotheses": validated,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Critique failed: {e}")
            self._fail_action(message, str(e))
            return {
                "success": False,
                "error": str(e),
                "message": message,
            }


class RootCauseAgent(BaseAgent):
    """Final agent that determines and outputs the root cause"""

    def __init__(self):
        super().__init__(
            name="RootCause",
            role="Determine final root cause and generate recommendations",
        )

    def determine_root_cause(self, state: ExecutionState) -> Dict[str, Any]:
        """Determine the root cause"""
        message = self._log_action("root_cause_determination", {})

        try:
            # Get top hypothesis
            if not state.validated_hypotheses:
                root_cause = "Unable to determine root cause"
                confidence = 0.0
            else:
                top_hyp = state.validated_hypotheses[0]
                root_cause = top_hyp.get("description", "")
                confidence = top_hyp.get("refined_confidence", 0.0)

            # Generate suggested fixes
            prompt = f"""
Given this root cause analysis, generate 2-3 concrete fixes:

Root Cause: {root_cause}
Affected Files: {', '.join(state.affected_files)}

Provide fixes in JSON format with:
- description: What to fix
- affected_files: Which files to change
- code_example: Before and after code snippet

Return ONLY valid JSON array, no markdown.
"""

            response = self.llm.invoke(prompt)
            fixes_text = response.content.strip()

            if "```json" in fixes_text:
                fixes_text = fixes_text.split("```json")[1].split("```")[0]
            elif "```" in fixes_text:
                fixes_text = fixes_text.split("```")[1].split("```")[0]

            possible_fixes = json.loads(fixes_text)

            self._complete_action(message, {"root_cause_confidence": confidence})

            return {
                "success": True,
                "root_cause": root_cause,
                "confidence": confidence,
                "possible_fixes": possible_fixes,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Root cause determination failed: {e}")
            self._fail_action(message, str(e))
            return {
                "success": False,
                "error": str(e),
                "message": message,
            }
