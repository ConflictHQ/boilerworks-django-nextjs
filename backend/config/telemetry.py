"""
Observability setup: OpenTelemetry tracing + Prometheus metrics.

Called once from CoreConfig.ready(). Configures:
  - TracerProvider with resource attributes (service name, version, environment)
  - DjangoInstrumentor wired to that provider
  - Span exporter: OTLP when OTEL_EXPORTER_OTLP_ENDPOINT is set,
    ConsoleSpanExporter for local dev without an endpoint
  - MeterProvider with PrometheusMetricReader → /metrics endpoint

Standard OTel env vars are respected:
  OTEL_SERVICE_NAME            override service name
  OTEL_EXPORTER_OTLP_ENDPOINT  e.g. http://otel-collector:4318
  OTEL_EXPORTER_OTLP_HEADERS   e.g. Authorization=Bearer <token>
"""

import logging
import os

logger = logging.getLogger(__name__)

_initialized = False


def setup(service_name: str, service_version: str, environment: str, is_local: bool) -> None:
    """Idempotent — safe to call from StatReloader child processes."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    _setup_tracing(service_name, service_version, environment, is_local)
    if environment.lower() != "tests":
        _setup_metrics(service_name, service_version, environment)


def _resource(service_name, service_version, environment):
    from opentelemetry.sdk.resources import DEPLOYMENT_ENVIRONMENT, SERVICE_NAME, SERVICE_VERSION, Resource
    return Resource.create({
        SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", service_name),
        SERVICE_VERSION: service_version,
        DEPLOYMENT_ENVIRONMENT: environment,
    })


def _setup_tracing(service_name, service_version, environment, is_local):
    from opentelemetry import trace
    from opentelemetry.instrumentation.django import DjangoInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=_resource(service_name, service_version, environment))

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        logger.info("OTel tracing → OTLP %s", endpoint)
    elif is_local:
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OTel tracing → ConsoleSpanExporter (local, no OTEL_EXPORTER_OTLP_ENDPOINT)")
    else:
        logger.warning(
            "OTel tracing: OTEL_EXPORTER_OTLP_ENDPOINT not set — spans will not be exported. "
            "Set it to your collector (e.g. http://otel-collector:4318)."
        )

    trace.set_tracer_provider(provider)
    DjangoInstrumentor().instrument(tracer_provider=provider)
    logger.info("OTel tracing ready (%s %s %s)", service_name, service_version, environment)


def _setup_metrics(service_name, service_version, environment):
    from opentelemetry import metrics
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.sdk.metrics import MeterProvider

    try:
        provider = MeterProvider(
            resource=_resource(service_name, service_version, environment),
            metric_readers=[PrometheusMetricReader()],
        )
        metrics.set_meter_provider(provider)
        logger.info("OTel metrics → PrometheusMetricReader (/metrics)")
    except Exception as exc:
        logger.warning("OTel metrics setup skipped: %s", exc)
