import httpx

from app.checker import check, parse_targets


def client_returning(status: int) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status)))


def test_parse_targets_ignores_blanks_and_spaces():
    assert parse_targets(" https://a.com, ,https://b.com ") == ["https://a.com", "https://b.com"]


def test_2xx_is_up():
    result = check(client_returning(200), "https://ok.test")
    assert result.up and result.status_code == 200 and result.latency_seconds is not None


def test_5xx_is_down():
    result = check(client_returning(503), "https://broken.test")
    assert not result.up and result.status_code == 503


def test_connection_error_is_down():
    def fail(request):
        raise httpx.ConnectError("refused")

    result = check(httpx.Client(transport=httpx.MockTransport(fail)), "https://down.test")
    assert not result.up and result.error == "ConnectError"
