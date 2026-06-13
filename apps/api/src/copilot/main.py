from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from copilot.api.analyses import router as analyses_router
from copilot.api.errors import (
    trial_not_found_handler,
    upstream_unavailable_handler,
)
from copilot.api.health import router as health_router
from copilot.api.trials import router as trials_router
from copilot.clients.clinical_trials import TrialNotFoundError, UpstreamUnavailableError
from copilot.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Oncology Trial Feasibility Copilot API",
    version="0.1.0",
    description=(
        "Illustrative decision-support API. Not a validated clinical or "
        "enrollment-prediction system."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Idempotency-Key",
        "X-Demo-User-Id",
    ],
)
app.include_router(health_router)
app.include_router(trials_router)
app.include_router(analyses_router)
app.add_exception_handler(TrialNotFoundError, trial_not_found_handler)
app.add_exception_handler(UpstreamUnavailableError, upstream_unavailable_handler)
