from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

from copilot.clients.clinical_trials import TrialNotFoundError, UpstreamUnavailableError


def error_payload(
    code: str,
    message: str,
    *,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    return {
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "correlation_id": str(uuid4()),
            "details": details or {},
        }
    }


async def trial_not_found_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, TrialNotFoundError)
    return JSONResponse(
        status_code=404,
        content=error_payload("TRIAL_NOT_FOUND", f"Study {exc} was not found."),
    )


async def upstream_unavailable_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, UpstreamUnavailableError)
    return JSONResponse(
        status_code=503,
        content=error_payload(
            "UPSTREAM_UNAVAILABLE",
            str(exc),
            retryable=True,
        ),
    )
