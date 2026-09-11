"""Shared FastAPI dependencies: a module-level service registry.

Creating the model service and running the prediction pipeline lazily (once)
keeps startup fast while guaranteeing every endpoint sees consistent data.
"""

import threading

from .. import database
from ..services.model_loader import ModelService
from .pipeline import PredictionPipeline, run_pipeline

_lock = threading.Lock()
_ready = False


def ensure_ready() -> None:
    """Seed DB + run the prediction pipeline at most once per process."""
    global _ready
    if _ready:
        return
    with _lock:
        if _ready:
            return
        conn = database.get_connection()
        try:
            database.seed_database()
            run_pipeline(conn)
        finally:
            conn.close()
        _ready = True


def get_model_service() -> ModelService:
    ensure_ready()
    return ModelService()