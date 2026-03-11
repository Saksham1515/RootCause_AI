#!/usr/bin/env python
"""
RootCause AI - Entry Point

Quick start script to run the Streamlit UI.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Streamlit UI."""
    # Get the path to the UI app
    ui_app = Path(__file__).parent / "src" / "rootcause_ai" / "ui" / "app.py"
    
    if not ui_app.exists():
        print(f"Error: UI app not found at {ui_app}")
        sys.exit(1)
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(ui_app),
        "--server.headless", "true",
    ])


if __name__ == "__main__":
    main()
