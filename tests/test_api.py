from fastapi.testclient import TestClient

from app import main


def test_healthz():
    assert TestClient(main.app).get("/healthz").json() == {"status": "ok"}


def test_readyz_is_503_before_first_round():
    main.results.clear()
    assert TestClient(main.app).get("/readyz").status_code == 503


def test_metrics_are_prometheus_text():
    response = TestClient(main.app).get("/metrics")
    assert response.status_code == 200
    assert "pulse_target_up" in response.text
