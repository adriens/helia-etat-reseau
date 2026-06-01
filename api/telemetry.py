"""OpenTelemetry setup — traces + métriques exportables vers un OTLP collector.

Variables d'environnement :
  OTEL_ENABLED            : "1" pour activer (défaut: 0)
  OTEL_SERVICE_NAME       : nom du service (défaut: helia-nc-api)
  OTEL_EXPORTER_OTLP_ENDPOINT : URL du collector OTLP (défaut: http://localhost:4317)
  OTEL_EXPORTER_PROTOCOL  : "grpc" ou "http/protobuf" (défaut: http/protobuf)

Compatibilité :
  - Grafana Tempo (traces)
  - Prometheus via OTLP receiver
  - Jaeger, Zipkin, etc.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def setup_telemetry(app) -> None:
    """Configure et attache l'instrumentation OTEL à l'app FastAPI."""
    if os.environ.get("OTEL_ENABLED", "0") != "1":
        return

    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    service_name = os.environ.get("OTEL_SERVICE_NAME", "helia-nc-api")
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    protocol = os.environ.get("OTEL_EXPORTER_PROTOCOL", "http/protobuf")

    resource = Resource.create({"service.name": service_name, "service.version": "0.2.0"})
    provider = TracerProvider(resource=resource)

    if protocol == "grpc":
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=endpoint)
    else:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=endpoint)

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        excluded_urls="/health,/metrics",
    )
    logger.info("OpenTelemetry enabled — service=%s endpoint=%s", service_name, endpoint)
