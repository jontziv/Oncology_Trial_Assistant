from fastapi.testclient import TestClient

from copilot.main import app


def test_liveness() -> None:
    response = TestClient(app).get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_production_web_origin_is_allowed() -> None:
    response = TestClient(app).options(
        "/v1/trials?query=lung",
        headers={
            "Origin": "https://oncology-trial-assistant-web.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type,x-demo-user-id",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://oncology-trial-assistant-web.vercel.app"
    )
