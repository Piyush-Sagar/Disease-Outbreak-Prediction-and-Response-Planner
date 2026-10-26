"""FastAPI application entrypoint.

Mounts the API routers under `/api`, serves the model figures as static
files, and exposes a `/health` probe. The prediction pipeline runs lazily on
first request (see `services/deps.ensure_ready`).
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .routers import dashboard, model_info, predictions, recommendations, regions, routes

app = FastAPI(
    title="AI-Based Disease Outbreak Prediction and Response Planner",
    description=(
        "Academic prototype: predicts high-incidence dengue events one week in "
        "advance, assesses severity, ranks regions, and plans responses. All "
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo: allow the Next.js dev server to call the API
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (regions, predictions, recommendations, routes, model_info, dashboard):
    app.include_router(module.router)

if os.path.isdir(config.MODEL_FIGURES_DIR):
    app.mount("/static/figures", StaticFiles(directory=config.MODEL_FIGURES_DIR), name="figures")


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(
        "<h1>AI-Based Disease Outbreak Prediction and Response Planner API</h1>"
        "<p>See <a href='/docs'>/docs</a> for the OpenAPI interactive documentation.</p>"
    )


@app.get("/health")
def health():
    return {"status": "ok", "demo_mode": config.DEMO_MODE, "disease": config.DISEASE}