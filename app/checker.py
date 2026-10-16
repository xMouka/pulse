"""Probes a list of HTTP targets and keeps the latest result for each one."""

import time
from dataclasses import asdict, dataclass

import httpx


@dataclass
class Result:
    target: str
    up: bool
    status_code: int | None
    latency_seconds: float | None
    error: str | None
    checked_at: float

    def to_dict(self) -> dict:
        return asdict(self)


def check(client: httpx.Client, target: str) -> Result:
    """One HTTP GET. Any 2xx/3xx counts as up; errors and 4xx/5xx count as down."""
    start = time.perf_counter()
    try:
        response = client.get(target)
        latency = time.perf_counter() - start
        return Result(target, response.status_code < 400, response.status_code, latency, None, time.time())
    except httpx.HTTPError as exc:
        return Result(target, False, None, None, type(exc).__name__, time.time())


def check_all(client: httpx.Client, targets: list[str]) -> dict[str, Result]:
    return {target: check(client, target) for target in targets}


def parse_targets(raw: str) -> list[str]:
    """'https://a.com, https://b.com' -> ['https://a.com', 'https://b.com']"""
    return [t.strip() for t in raw.split(",") if t.strip()]
