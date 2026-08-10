"""
Run the Recruiter Pro AI API Server.

    python run_api.py

Must be run from the repository root - `src` is resolved relative to the
working directory, and several paths in the app (the job corpus, the skill
vocabulary, the model directory) are relative too.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run
from src.api import app
import uvicorn

if __name__ == "__main__":
    # No emoji here. Windows consoles default to the cp1252 code page, which
    # cannot encode them, and this file died with UnicodeEncodeError before
    # uvicorn ever started - on the platform the project's own Run.ps1 targets.
    print("=" * 60)
    print("Starting Recruiter Pro AI API Server...")
    print("  Docs:  http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
