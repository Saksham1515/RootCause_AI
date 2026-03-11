"""
RootCause AI - Streamlit Application

Main entry point for the Streamlit web interface.
"""

import traceback
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from rootcause_ai.config.providers import LLM_PROVIDERS
from rootcause_ai.core.workflow import run_analysis
from rootcause_ai.services.llm import detect_models
from rootcause_ai.ui.components import (
    render_header,
    render_sidebar,
    render_input_form,
    render_results,
    render_footer,
)
from rootcause_ai.utils.logging import setup_logging, get_logger

# Initialize logging
setup_logging()
log = get_logger("ui.app")

# Load environment variables
load_dotenv()
log.info("RootCause AI application started")


def main() -> None:
    """Main application entry point."""
    # Page config
    st.set_page_config(
        page_title="RootCause AI",
        page_icon="🔍",
        layout="wide",
    )
    
    # Initialize session state
    if "ollama_models" not in st.session_state:
        st.session_state.ollama_models = None
    
    # Render UI
    render_header()
    
    # Sidebar configuration
    llm_provider, selected_model, api_key = render_sidebar(
        llm_providers=LLM_PROVIDERS,
        detect_models_func=detect_models,
    )
    
    # Input form
    codebase_path, issue_description, analyze_clicked = render_input_form()
    
    # Run analysis when button is clicked
    if analyze_clicked:
        _run_analysis(
            codebase_path=codebase_path,
            issue_description=issue_description,
            llm_provider=llm_provider,
            selected_model=selected_model,
            api_key=api_key,
        )
    
    render_footer()


def _run_analysis(
    codebase_path: str,
    issue_description: str,
    llm_provider: str,
    selected_model: str,
    api_key: str | None,
) -> None:
    """Execute the analysis workflow."""
    # Validation
    if not codebase_path:
        st.error("Please enter a codebase path")
        return
    
    if not issue_description:
        st.error("Please describe the issue")
        return
    
    if not Path(codebase_path).exists():
        st.error(f"Path does not exist: {codebase_path}")
        return
    
    if not api_key and llm_provider != "ollama":
        st.error(f"Please enter your {LLM_PROVIDERS[llm_provider]['name']} API key in the sidebar")
        return
    
    st.divider()
    st.subheader("📊 Analysis Results")
    
    log.info("User initiated analysis")
    log.info(f"Provider: {llm_provider}, Model: {selected_model}")
    log.info(f"Codebase: {codebase_path}")
    log.debug(f"Issue description: {issue_description[:200]}...")
    
    with st.spinner("🔍 Analyzing codebase..."):
        try:
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Step 1/4: Scanning codebase...")
            progress_bar.progress(25)
            
            log.info("Calling run_analysis...")
            
            # Run the analysis
            result = run_analysis(codebase_path, issue_description)
            
            log.info("run_analysis completed")
            log.debug(f"Result keys: {list(result.keys())}")
            
            progress_bar.progress(100)
            status_text.text("Analysis complete!")
            
            # Check for errors
            if result.get("error"):
                log.error(f"Analysis returned error: {result['error']}")
                st.error(f"Error: {result['error']}")
            else:
                log.info("Analysis successful, displaying results")
                st.success("Analysis completed successfully!")
                
                # Display results
                log.info(f"Root cause: {result.get('root_cause', '')[:100]}...")
                log.info(f"Suggested fix length: {len(result.get('suggested_fix', ''))} chars")
                render_results(result)
                
        except ImportError as e:
            log.error(f"Import error: {e}")
            log.error(traceback.format_exc())
            st.error(f"Import error: {e}. Make sure all dependencies are installed.")
        
        except Exception as e:
            log.error(f"Unexpected error during analysis: {e}")
            log.error(traceback.format_exc())
            st.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
