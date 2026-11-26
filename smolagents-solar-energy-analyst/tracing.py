"""Send smolagents spans to Opik over OpenTelemetry."""

import os

PROJECT_NAME = "smolagents-solar-energy-analyst"


def otlp_settings() -> tuple[str, str]:
    """Return (endpoint, headers) for Opik's OTLP/HTTP ingest, from the environment."""
    base = os.getenv("OPIK_URL_OVERRIDE", "http://localhost:5173/api/").rstrip("/")
    # projectName routes every span into one Opik project; Comet-Workspace picks the workspace.
    headers = [
        f"Comet-Workspace={os.getenv('OPIK_WORKSPACE', 'default')}",
        f"projectName={PROJECT_NAME}",
    ]
    if os.getenv("OPIK_API_KEY"):  # Opik Cloud only; local self-hosted needs no key
        headers.insert(0, f"Authorization={os.environ['OPIK_API_KEY']}")
    return f"{base}/v1/private/otel", ",".join(headers)


def setup_tracing():
    """Instrument smolagents and return the provider (call .shutdown() to flush)."""
    from openinference.instrumentation.smolagents import SmolagentsInstrumentor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    endpoint, headers = otlp_settings()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = headers

    provider = TracerProvider()
    # The exporter POSTs spans to Opik's OTLP endpoint; SimpleSpanProcessor sends each
    # span as it ends, so a crash mid-question still leaves the earlier steps in Opik.
    provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
    # The instrumentor wraps CodeAgent.run, each step and each model call: they show up
    # as a trace with nested Step and generate spans, code and logs included.
    SmolagentsInstrumentor().instrument(tracer_provider=provider)
    return provider
