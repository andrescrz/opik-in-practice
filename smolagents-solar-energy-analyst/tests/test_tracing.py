from tracing import PROJECT_NAME, otlp_settings


def test_endpoint_derives_from_opik_url(monkeypatch):
    monkeypatch.setenv("OPIK_URL_OVERRIDE", "http://example.test/api/")
    monkeypatch.setenv("OPIK_WORKSPACE", "team")
    monkeypatch.delenv("OPIK_API_KEY", raising=False)
    endpoint, headers = otlp_settings()
    assert endpoint == "http://example.test/api/v1/private/otel"
    assert headers == f"Comet-Workspace=team,projectName={PROJECT_NAME}"


def test_api_key_becomes_authorization_header(monkeypatch):
    monkeypatch.setenv("OPIK_API_KEY", "k")
    _, headers = otlp_settings()
    assert headers.startswith("Authorization=k,")
