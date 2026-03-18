"""
Streamlit UI for RootCause AI
"""
import streamlit as st
import logging
from typing import Optional
import json
from datetime import datetime
from pathlib import Path
import asyncio

from config.schema import ExecutionState
from graph.debug_workflow import DebugWorkflow
from memory.memory_manager import MemoryManager
from utils.embeddings import EmbeddingsManager
from utils.code_processor import FileIndexer

logger = logging.getLogger(__name__)


def init_session_state():
    """Initialize Streamlit session state"""
    if "workflow" not in st.session_state:
        st.session_state.workflow = DebugWorkflow()
    if "memory_manager" not in st.session_state:
        st.session_state.memory_manager = MemoryManager()
    if "embeddings_manager" not in st.session_state:
        st.session_state.embeddings_manager = EmbeddingsManager()
    if "execution_state" not in st.session_state:
        st.session_state.execution_state = None
    if "results" not in st.session_state:
        st.session_state.results = None
    if "is_running" not in st.session_state:
        st.session_state.is_running = False


def render_header():
    """Render UI header"""
    st.set_page_config(page_title="RootCause AI", layout="wide", initial_sidebar_state="expanded")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔍 RootCause AI")
        st.markdown("*Advanced Multi-Agent Debugging System*")
    with col2:
        st.markdown("### 🤖 Multi-Agent Orchestration")


def render_sidebar():
    """Render sidebar with controls"""
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Codebase path
        codebase_path = st.text_input(
            "📁 Codebase Path",
            value="./sample_code",
            help="Path to the codebase to analyze"
        )

        # Model selection
        model = st.selectbox(
            "🧠 LLM Model",
            ["gpt-4", "gpt-3.5-turbo"],
            help="Language model to use"
        )

        # Output format
        st.subheader("🎯 Analysis Settings")
        top_k = st.slider("Top-K Results", 1, 10, 5, help="Number of relevant files to retrieve")
        confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.7, help="Minimum confidence for hypotheses")

        st.divider()
        st.subheader("📊 Session Info")
        if st.session_state.memory_manager:
            stats = st.session_state.memory_manager.get_memory_stats()
            st.metric("Session Events", stats["short_term"]["entries"])
            st.metric("Stored Patterns", stats["long_term"]["total_bug_patterns"])
            st.metric("Stored Solutions", stats["long_term"]["total_solutions"])

        return {
            "codebase_path": codebase_path,
            "model": model,
            "top_k": top_k,
            "confidence_threshold": confidence_threshold,
        }


def render_input_panel():
    """Render input panel for user query"""
    st.subheader("🎯 Define Your Issue")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        user_query = st.text_area(
            "Describe the issue or bug",
            placeholder="e.g., RuntimeError: maximum recursion depth exceeded when processing large datasets...",
            height=100,
            key="user_query"
        )
    
    with col2:
        st.markdown("**📎 Additional Context**")
        
        has_error_logs = st.checkbox("Include Error Logs", value=False)
        error_logs = None
        if has_error_logs:
            error_logs = st.text_area(
                "Error Logs",
                placeholder="Paste error logs here...",
                height=150,
                key="error_logs"
            )
        
        has_stack_trace = st.checkbox("Include Stack Trace", value=False)
        stack_trace = None
        if has_stack_trace:
            stack_trace = st.text_area(
                "Stack Trace",
                placeholder="Paste stack trace here...",
                height=150,
                key="stack_trace"
            )

    return {
        "user_query": user_query,
        "error_logs": error_logs,
        "stack_trace": stack_trace,
    }


def render_execution_tabs():
    """Render tabbed interface for execution and results"""
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Execute", "📊 Results", "🧠 Memories", "📈 Graph"])

    with tab1:
        render_execution_tab()

    with tab2:
        render_results_tab()

    with tab3:
        render_memory_tab()

    with tab4:
        render_graph_tab()


def render_execution_tab():
    """Render execution tab"""
    st.subheader("🚀 Workflow Execution")

    config = render_sidebar()
    inputs = render_input_panel()

    if st.button("🔬 Start Debugging Analysis", type="primary", use_container_width=True):
        if not inputs["user_query"]:
            st.error("Please describe your issue")
            return

        st.session_state.is_running = True

        # Create execution state
        execution_state = ExecutionState(
            user_query=inputs["user_query"],
            codebase_path=config["codebase_path"],
            error_logs=inputs["error_logs"],
            stack_trace=inputs["stack_trace"],
        )

        progress_bar = st.progress(0)
        status_container = st.container()

        with status_container:
            st.info("🔄 Workflow starting...")

            try:
                # Index codebase
                status_container.info("📂 Step 1: Indexing codebase...")
                progress_bar.progress(15)

                indexer = FileIndexer()
                indexed_files = indexer.index_directory(config["codebase_path"])
                execution_state.indexed_files = indexed_files

                status_container.info("📊 Step 2: Building embeddings...")
                progress_bar.progress(30)

                # Here we would build embeddings (simplified for now)

                status_container.info("🤖 Step 3: Running multi-agent analysis...")
                progress_bar.progress(50)

                # Run workflow
                workflow = st.session_state.workflow
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                final_state = loop.run_until_complete(workflow.execute(execution_state))

                progress_bar.progress(90)

                # Store results
                st.session_state.execution_state = final_state
                st.session_state.results = final_state

                # Record session event
                st.session_state.memory_manager.record_session_event(
                    agent_name="UI",
                    action="analysis_completed",
                    details={
                        "query": inputs["user_query"][:50],
                        "root_cause_found": bool(final_state.root_cause),
                        "confidence": final_state.root_cause_confidence,
                    },
                )

                progress_bar.progress(100)
                st.session_state.is_running = False

                st.success("✅ Analysis Complete!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"Workflow error: {e}")
                st.session_state.is_running = False


def render_results_tab():
    """Render results tab"""
    st.subheader("📊 Analysis Results")

    if not st.session_state.results:
        st.info("👈 Run an analysis from the Execute tab to see results here")
        return

    results = st.session_state.results

    # Root Cause Card
    st.markdown("### 🎯 Root Cause Analysis")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Confidence", f"{results.root_cause_confidence:.1%}")
    with col2:
        st.metric("Affected Files", len(results.affected_files))
    with col3:
        st.metric("Issues Found", len(results.detected_issues))

    st.markdown("**Root Cause:**")
    st.info(results.root_cause or "No root cause determined")

    # Affected Files
    if results.affected_files:
        st.markdown("### 📁 Affected Files")
        for file in results.affected_files:
            st.write(f"- `{file}`")

    # Possible Fixes
    if results.possible_fixes:
        st.markdown("### 🔧 Suggested Fixes")
        for i, fix in enumerate(results.possible_fixes, 1):
            with st.expander(f"Fix {i}: {fix.get('description', 'Fix')}"):
                st.json(fix)

    # Reasoning Steps
    if results.reasoning_steps:
        st.markdown("### 🧠 Reasoning Steps")
        for i, step in enumerate(results.reasoning_steps, 1):
            st.write(f"{i}. {step}")

    # Agent Logs
    if results.agent_logs:
        st.markdown("### 📜 Agent Activity Log")
        with st.expander("View Detailed Logs"):
            for log in results.agent_logs:
                st.write(f"- {log}")


def render_memory_tab():
    """Render memory/history tab"""
    st.subheader("🧠 Memory & History")

    memory_manager = st.session_state.memory_manager

    # Session Summary
    st.markdown("### 📊 Current Session")
    session_summary = memory_manager.get_session_summary()
    st.metric("Session Events", len(session_summary["events"]))

    if session_summary["events"]:
        with st.expander("View Session Events"):
            for event in session_summary["events"]:
                st.write(f"**{event.get('agent', 'Unknown')}** - {event.get('action', 'N/A')}")

    # Long-term Memory
    st.markdown("### 💾 Long-Term Memory")
    stats = memory_manager.long_term.get_statistics()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Stored Bug Patterns", stats["total_bug_patterns"])
    with col2:
        st.metric("Stored Solutions", stats["total_solutions"])

    # Recent Patterns
    if stats["recent_patterns"]:
        st.markdown("**Recent Bug Patterns:**")
        for pattern in stats["recent_patterns"]:
            st.write(f"- {pattern.get('description', 'Pattern')}")

    # Recent Solutions
    if stats["recent_solutions"]:
        st.markdown("**Recent Solutions:**")
        for solution in stats["recent_solutions"]:
            st.write(f"- {solution.get('problem_description', 'Solution')}")


def render_graph_tab():
    """Render workflow graph tab"""
    st.subheader("📈 Workflow Graph")

    try:
        # Get graph visualization
        workflow = st.session_state.workflow
        graph_viz = workflow.get_graph_visualization()

        st.markdown("**Workflow Structure:**")
        st.code(graph_viz, language="text")

    except Exception as e:
        st.warning(f"Could not generate graph visualization: {e}")

    # Execution Graph Info
    if st.session_state.results:
        st.markdown("**Execution Path:**")
        exec_graph = st.session_state.results.execution_graph
        if exec_graph:
            st.json(exec_graph)


def main():
    """Main Streamlit app"""
    init_session_state()
    render_header()
    render_execution_tabs()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    main()
