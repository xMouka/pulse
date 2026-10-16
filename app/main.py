"""pulse: an uptime checker that exposes its results as JSON and Prometheus metrics.

Config comes from environment variables, so Kubernetes can set it with a ConfigMap:
  PULSE_TARGETS   comma-separated URLs to check
  PULSE_INTERVAL  seconds between check rounds (default 30)
  PULSE_TIMEOUT   seconds before a request gives up (default 5)
"""

import os
import threading
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

from app.checker import Result, check_all, parse_targets

TARGETS = parse_targets(os.getenv("PULSE_TARGETS", "https://example.com"))
INTERVAL = float(os.getenv("PULSE_INTERVAL", "30"))
TIMEOUT = float(os.getenv("PULSE_TIMEOUT", "5"))

UP = Gauge("pulse_target_up", "1 if the target answered with a status below 400", ["target"])
LATENCY = Gauge("pulse_target_latency_seconds", "Response time of the last check", ["target"])

results: dict[str, Result] = {}
stop = threading.Event()


def run_checks() -> None:
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
        while not stop.is_set():
            for target, result in check_all(client, TARGETS).items():
                results[target] = result
                UP.labels(target).set(1 if result.up else 0)
                if result.latency_seconds is not None:
                    LATENCY.labels(target).set(result.latency_seconds)
            stop.wait(INTERVAL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    worker = threading.Thread(target=run_checks, daemon=True)
    worker.start()
    yield
    stop.set()


app = FastAPI(title="pulse", lifespan=lifespan)


@app.get("/healthz")
def healthz():
    """Liveness: the process is running."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz(response: Response):
    """Readiness: at least one check round has finished."""
    if len(results) < len(TARGETS):
        response.status_code = 503
        return {"status": "starting"}
    return {"status": "ready"}


@app.get("/status")
def status():
    return {
        "targets": len(TARGETS),
        "up": sum(r.up for r in results.values()),
        "results": [r.to_dict() for r in results.values()],
    }


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
