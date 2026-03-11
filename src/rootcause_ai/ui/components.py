"""
Reusable Streamlit UI components.
"""

import streamlit as st

# Custom CSS with dark theme support
CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #888;
        margin-bottom: 2rem;
    }
    .result-box {
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .success-box {
        background-color: rgba(40, 167, 69, 0.15);
        border-left: 4px solid #28a745;
        color: inherit;
    }
    .warning-box {
        background-color: rgba(255, 193, 7, 0.15);
        border-left: 4px solid #ffc107;
        color: inherit;
    }
    .error-box {
        background-color: rgba(220, 53, 69, 0.15);
        border-left: 4px solid #dc3545;
        color: inherit;
    }
</style>
"""


def render_header() -> None:
    """Render the application header."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(
        '<p class="main-header">🔍 RootCause AI</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-header">AI-powered debugging assistant for your codebase</p>',
        unsafe_allow_html=True,
    )


def render_sidebar(
    llm_providers: dict,
    detect_models_func,
) -> tuple[str, str, str | None]:
    """
    Render the sidebar configuration.
    
    Args:
        llm_providers: Dictionary of LLM provider configurations
        detect_models_func: Function to detect models for a provider
    
    Returns:
        Tuple of (selected_provider, selected_model, api_key)
    """
    import os
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Provider selection
        provider_options = list(llm_providers.keys())
        
        llm_provider = st.selectbox(
            "LLM Provider",
            provider_options,
            format_func=lambda x: llm_providers[x]["name"],
            index=0,
        )
        os.environ["LLM_PROVIDER"] = llm_provider
        
        st.divider()
        
        # API Key / Configuration based on provider
        api_key = _render_api_key_input(llm_provider, detect_models_func)
        
        st.divider()
        
        # Get available models
        available_models = _get_available_models(llm_provider, llm_providers)
        default_model = llm_providers[llm_provider]["default"]
        
        # Model selection
        selected_model = st.selectbox(
            "Model",
            available_models,
            index=available_models.index(default_model) if default_model in available_models else 0,
        )
        os.environ["LLM_MODEL"] = selected_model
        
        st.divider()
        st.markdown("""
        **How it works:**
        1. Enter your codebase path
        2. Describe the issue
        3. AI scans relevant files
        4. Get root cause & fix suggestions
        """)
    
    return llm_provider, selected_model, api_key


def _render_api_key_input(provider: str, detect_models_func) -> str | None:
    """Render API key input based on provider."""
    import os
    
    api_key = None
    
    if provider == "openai":
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Enter your OpenAI API key",
        )
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            
    elif provider == "anthropic":
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            help="Enter your Anthropic API key",
        )
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            
    elif provider == "gemini":
        api_key = st.text_input(
            "Google API Key",
            type="password",
            value=os.getenv("GOOGLE_API_KEY", ""),
            help="Enter your Google AI API key",
        )
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            
    elif provider == "ollama":
        ollama_url = st.text_input(
            "Ollama Base URL",
            value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            help="Ollama server URL (default: http://localhost:11434)",
        )
        os.environ["OLLAMA_BASE_URL"] = ollama_url
        api_key = "ollama"  # Ollama doesn't need API key
        
        # Auto-detect Ollama models
        if st.session_state.get("ollama_models") is None:
            detected = detect_models_func("ollama", None)
            st.session_state.ollama_models = detected if detected else None
        
        # Refresh button for Ollama only
        if st.button("🔄 Refresh Models", use_container_width=True):
            with st.spinner("Detecting Ollama models..."):
                detected = detect_models_func("ollama", None)
                if detected:
                    st.session_state.ollama_models = detected
                    st.success(f"Found {len(detected)} models!")
                else:
                    st.warning("Could not connect to Ollama")
    
    return api_key


def _get_available_models(provider: str, llm_providers: dict) -> list[str]:
    """Get available models for a provider."""
    if provider == "ollama" and st.session_state.get("ollama_models"):
        return st.session_state.ollama_models
    return llm_providers[provider]["models"]


def render_input_form() -> tuple[str, str, bool]:
    """
    Render the input form.
    
    Returns:
        Tuple of (codebase_path, issue_description, analyze_clicked)
    """
    st.subheader("📁 Input")
    
    codebase_path = st.text_input(
        "Codebase Path",
        placeholder="/Users/yourname/projects/your-app",
        help="Enter the full path to your local codebase",
    )
    
    issue_description = st.text_area(
        "Issue Description",
        placeholder="Describe the bug or issue you're experiencing...\n\nExample: Checkout API returns 500 error when placing an order",
        height=120,
        help="Be as specific as possible about the issue",
    )
    
    analyze_button = st.button(
        "🔍 Analyze Issue",
        type="primary",
        use_container_width=True,
    )
    
    return codebase_path, issue_description, analyze_button


def render_results(result: dict) -> None:
    """
    Render analysis results.
    
    Args:
        result: Analysis result dictionary
    """
    # Files scanned
    with st.expander("📂 Files Scanned", expanded=False):
        st.text(result.get("file_summary", "No files found"))
    
    # Relevant files
    with st.expander("🎯 Relevant Files Selected", expanded=False):
        relevant = result.get("relevant_files", [])
        if relevant:
            for f in relevant:
                st.text(f"• {f}")
        else:
            st.text("No relevant files identified")
    
    # Root Cause
    st.markdown("### 🎯 Root Cause")
    root_cause = result.get("root_cause", "Unable to determine root cause")
    st.warning(root_cause)
    
    # Explanation
    st.markdown("### 📝 Explanation")
    explanation = result.get("explanation", "No explanation available")
    st.info(explanation)
    
    # Suggested Fix
    st.markdown("### 🛠️ Suggested Fix")
    suggested_fix = result.get("suggested_fix", "No fix suggestion available")
    with st.container(border=True):
        st.markdown(suggested_fix)


def render_footer() -> None:
    """Render the application footer."""
    st.divider()
    st.markdown(
        """
        <div style="text-align: center; color: #888; font-size: 0.9rem;">
            RootCause AI - Built with LangGraph, LangChain & Streamlit
        </div>
        """,
        unsafe_allow_html=True,
    )
