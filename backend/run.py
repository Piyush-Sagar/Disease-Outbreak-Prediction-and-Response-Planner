"""Development server launcher.

Adds the backend dir (so `app` imports) and the repo root (so the `ml`
package imports) to sys.path, then runs uvicorn.

Usage (from the repo root or the backend dir):
    python backend/run.py
"""

import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BACKEND_DIR)

for path in (BACKEND_DIR, REPO_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

import uvicorn  # noqa: E402

from app import config  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
    )