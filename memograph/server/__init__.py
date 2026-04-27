"""REST API server for MemoGraph.

This module provides a FastAPI-based REST API that exposes
MemoGraph functionality over HTTP. Useful for connecting
any AI tool, agent, or client that supports HTTP.

Example:
    >>> from memograph.server import create_app
    >>> app = create_app(vault_path="./my-vault")

    Or run directly:
    >>> uvicorn memograph.server.app:app --host 0.0.0.0 --port 8000

    Or using the CLI:
    >>> python -m memograph.server --vault ~/my-vault --port 8000
"""

from .app import create_app

__all__ = ["create_app"]
