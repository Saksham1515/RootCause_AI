"""
Command-line interface for RootCause AI.
"""

import argparse
import sys

from rootcause_ai.core.workflow import run_analysis
from rootcause_ai.utils.logging import setup_logging, get_logger


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="rootcause",
        description="AI-powered debugging assistant for codebases",
    )
    parser.add_argument(
        "codebase_path",
        help="Path to the codebase to analyze",
    )
    parser.add_argument(
        "issue",
        help="Description of the issue to analyze",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "gemini", "ollama"],
        default="openai",
        help="LLM provider to use (default: openai)",
    )
    parser.add_argument(
        "--model",
        help="Specific model to use (defaults to provider's default)",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)
    log = get_logger("cli")
    
    # Set environment variables for provider/model
    import os
    os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["LLM_MODEL"] = args.model
    
    log.info(f"Analyzing: {args.codebase_path}")
    log.info(f"Issue: {args.issue}")
    
    try:
        result = run_analysis(args.codebase_path, args.issue)
        
        if result.get("error"):
            print(f"\n❌ Error: {result['error']}")
            return 1
        
        print("\n" + "=" * 60)
        print("🎯 ROOT CAUSE")
        print("=" * 60)
        print(result.get("root_cause", "Unable to determine root cause"))
        
        print("\n" + "=" * 60)
        print("📝 EXPLANATION")
        print("=" * 60)
        print(result.get("explanation", "No explanation available"))
        
        print("\n" + "=" * 60)
        print("🛠️ SUGGESTED FIX")
        print("=" * 60)
        print(result.get("suggested_fix", "No fix suggestion available"))
        
        return 0
        
    except Exception as e:
        log.error(f"Analysis failed: {e}")
        print(f"\n❌ Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
