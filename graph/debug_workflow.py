"""
LangGraph workflow for RootCause AI multi-agent system
"""
import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from config.schema import ExecutionState
from agents.specialized_agents import (
    PlannerAgent,
    ContextBuilderAgent,
    RetrieverAgent,
    CodeReasoningAgent,
    BugDetectionAgent,
    LogAnalysisAgent,
    DependencyTrackerAgent,
    HypothesisAgent,
    CriticAgent,
    RootCauseAgent,
)
import asyncio

logger = logging.getLogger(__name__)


class DebugWorkflow:
    """Orchestrates multi-agent debugging workflow using LangGraph"""

    def __init__(self):
        self.planner = PlannerAgent()
        self.context_builder = ContextBuilderAgent()
        self.retriever = RetrieverAgent()
        self.code_reasoner = CodeReasoningAgent()
        self.bug_detector = BugDetectionAgent()
        self.log_analyzer = LogAnalysisAgent()
        self.dependency_tracker = DependencyTrackerAgent()
        self.hypothesis_agent = HypothesisAgent()
        self.critic = CriticAgent()
        self.root_cause_agent = RootCauseAgent()

        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(ExecutionState)

        # Add nodes
        workflow.add_node("planner", self._node_planner)
        workflow.add_node("context_builder", self._node_context_builder)
        workflow.add_node("retriever", self._node_retriever)
        workflow.add_node("code_reasoner", self._node_code_reasoner)
        workflow.add_node("bug_detector", self._node_bug_detector)
        workflow.add_node("log_analyzer", self._node_log_analyzer)
        workflow.add_node("dependency_tracker", self._node_dependency_tracker)
        workflow.add_node("hypothesis_generator", self._node_hypothesis_generator)
        workflow.add_node("critic", self._node_critic)
        workflow.add_node("root_cause", self._node_root_cause)

        # Add edges - define execution flow
        workflow.set_entry_point("planner")

        # Planner -> Context Builder
        workflow.add_edge("planner", "context_builder")

        # Context Builder -> Parallel Analysis (retriever + log analyzer, etc.)
        workflow.add_edge("context_builder", "retriever")

        # Parallel branches based on available data
        workflow.add_edge("retriever", "code_reasoner")
        workflow.add_conditional_edges(
            "code_reasoner",
            self._should_analyze_bugs,
            {
                True: "bug_detector",
                False: "dependency_tracker",
            },
        )

        workflow.add_conditional_edges(
            "context_builder",
            self._should_analyze_logs,
            {
                True: "log_analyzer",
                False: "bug_detector",
            },
        )

        # Merge branches
        workflow.add_edge("bug_detector", "dependency_tracker")
        workflow.add_edge("log_analyzer", "dependency_tracker")

        # After dependency tracking, generate hypotheses
        workflow.add_edge("dependency_tracker", "hypothesis_generator")

        # Critique hypotheses
        workflow.add_edge("hypothesis_generator", "critic")

        # Critic can loop back (for refinement) or continue to root cause
        workflow.add_conditional_edges(
            "critic",
            self._should_refine_hypotheses,
            {
                True: "hypothesis_generator",  # Loop for refinement
                False: "root_cause",  # Proceed to root cause
            },
        )

        # End at root cause agent
        workflow.add_edge("root_cause", END)

        return workflow

    def _node_planner(self, state: ExecutionState) -> Dict[str, Any]:
        """Planner node"""
        logger.info(f"Planner: Processing query - {state.user_query[:50]}...")
        result = self.planner.plan(state)
        state.agent_logs.append(f"Planner: {result.get('success', False)}")
        state.execution_graph["planner"] = result.get("plan", {})
        return state

    def _node_context_builder(self, state: ExecutionState) -> Dict[str, Any]:
        """Context Builder node"""
        logger.info("ContextBuilder: Indexing codebase...")
        result = self.context_builder.build_context(state)

        if result.get("success"):
            state.indexed_files = result.get("indexed_files", [])
            state.agent_logs.append(f"ContextBuilder: Indexed {result['summary'].get('total_files', 0)} files")
        else:
            state.agent_logs.append(f"ContextBuilder: Failed - {result.get('error', 'Unknown error')}")

        return state

    def _node_retriever(self, state: ExecutionState) -> Dict[str, Any]:
        """Retriever node"""
        logger.info("Retriever: Performing semantic search...")
        result = self.retriever.retrieve(state, state.user_query, top_k=5)

        if result.get("success"):
            state.relevant_files = result.get("results", [])
            state.agent_logs.append(f"Retriever: Found {len(state.relevant_files)} relevant files")
        else:
            state.agent_logs.append(f"Retriever: No results found")

        return state

    def _node_code_reasoner(self, state: ExecutionState) -> Dict[str, Any]:
        """Code Reasoning node"""
        logger.info("CodeReasoner: Analyzing code logic...")

        files_to_analyze = [f.file_path for f in state.relevant_files[:3]]
        result = self.code_reasoner.analyze_code(state, files_to_analyze)

        if result.get("success"):
            state.execution_flows = result.get("analysis", {}).get("call_chains", [])
            state.agent_logs.append(f"CodeReasoner: Analyzed {len(files_to_analyze)} files")
        else:
            state.agent_logs.append(f"CodeReasoner: Analysis failed")

        return state

    def _node_bug_detector(self, state: ExecutionState) -> Dict[str, Any]:
        """Bug Detection node"""
        logger.info("BugDetector: Scanning for bugs...")

        files_to_check = [f.file_path for f in state.relevant_files[:3]]
        result = self.bug_detector.detect_bugs(state, files_to_check)

        if result.get("success"):
            state.detected_issues.extend(result.get("issues", []))
            state.agent_logs.append(f"BugDetector: Found {len(result.get('issues', []))} issues")
        else:
            state.agent_logs.append(f"BugDetector: Detection failed")

        return state

    def _node_log_analyzer(self, state: ExecutionState) -> Dict[str, Any]:
        """Log Analysis node"""
        logger.info("LogAnalyzer: Analyzing logs...")

        result = self.log_analyzer.analyze_logs(state)

        if result.get("success"):
            state.agent_logs.append(f"LogAnalyzer: Analysis complete")
        else:
            state.agent_logs.append(f"LogAnalyzer: No logs to analyze")

        return state

    def _node_dependency_tracker(self, state: ExecutionState) -> Dict[str, Any]:
        """Dependency Tracker node"""
        logger.info("DependencyTracker: Mapping dependencies...")

        files_to_track = [f.file_path for f in state.relevant_files[:3]]
        result = self.dependency_tracker.track_dependencies(state, files_to_track)

        if result.get("success"):
            state.dependencies = result.get("dependencies", {})
            state.agent_logs.append(f"DependencyTracker: Mapped dependencies")
        else:
            state.agent_logs.append(f"DependencyTracker: Mapping failed")

        return state

    def _node_hypothesis_generator(self, state: ExecutionState) -> Dict[str, Any]:
        """Hypothesis Generator node"""
        logger.info("HypothesisGenerator: Generating hypotheses...")

        result = self.hypothesis_agent.generate_hypotheses(state)

        if result.get("success"):
            state.hypotheses = [h.dict() for h in result.get("hypotheses", [])]
            state.agent_logs.append(f"HypothesisGenerator: Generated {len(state.hypotheses)} hypotheses")
        else:
            state.agent_logs.append(f"HypothesisGenerator: Generation failed")

        return state

    def _node_critic(self, state: ExecutionState) -> Dict[str, Any]:
        """Critic node"""
        logger.info("Critic: Validating hypotheses...")

        result = self.critic.critique(state)

        if result.get("success"):
            state.validated_hypotheses = result.get("validated_hypotheses", [])
            state.agent_logs.append(f"Critic: Validated {len(state.validated_hypotheses)} hypotheses")
        else:
            state.agent_logs.append(f"Critic: Validation failed")

        return state

    def _node_root_cause(self, state: ExecutionState) -> Dict[str, Any]:
        """Root Cause Agent node"""
        logger.info("RootCauseAgent: Determining final root cause...")

        result = self.root_cause_agent.determine_root_cause(state)

        if result.get("success"):
            state.root_cause = result.get("root_cause", "")
            state.root_cause_confidence = result.get("confidence", 0.0)
            state.possible_fixes = result.get("possible_fixes", [])
            state.agent_logs.append(f"RootCauseAgent: Root cause determined with {state.root_cause_confidence:.1%} confidence")
        else:
            state.agent_logs.append(f"RootCauseAgent: Determination failed")

        return state

    # Conditional routing functions
    @staticmethod
    def _should_analyze_bugs(state: ExecutionState) -> bool:
        """Decide if bug detection is needed"""
        return len(state.execution_flows) > 0

    @staticmethod
    def _should_analyze_logs(state: ExecutionState) -> bool:
        """Decide if log analysis is needed"""
        return state.error_logs is not None or state.stack_trace is not None

    @staticmethod
    def _should_refine_hypotheses(state: ExecutionState) -> bool:
        """Decide if hypotheses need refinement"""
        if not state.validated_hypotheses:
            return False
        # Refine if confidence is low
        top_confidence = state.validated_hypotheses[0].get("refined_confidence", 0)
        return top_confidence < 0.7

    async def execute(self, state: ExecutionState) -> ExecutionState:
        """Execute the workflow"""
        logger.info("Starting debugging workflow...")
        
        try:
            # Compile the graph
            runnable = self.workflow.compile()
            
            # Run the workflow
            final_state = runnable.invoke(state)
            
            logger.info("Workflow completed successfully")
            return final_state
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            state.agent_logs.append(f"ERROR: Workflow failed - {str(e)}")
            return state

    def get_graph_visualization(self) -> str:
        """Get ASCII representation of the workflow graph"""
        return self.workflow.get_graph().print_ascii()
