# n8n with Opik tracing baked in, with no nodes and no workflow changes.
# n8n-observability hooks into n8n's lifecycle through EXTERNAL_HOOK_FILES and
# exports one OpenTelemetry span per workflow run and one per node; Opik ingests
# them on its OTLP endpoint (endpoint and headers come from docker-compose.yml).
FROM n8nio/n8n:2.41.7

USER root
RUN npm install -g n8n-observability@1.0.3
ENV EXTERNAL_HOOK_FILES=/usr/local/lib/node_modules/n8n-observability/dist/hooks.cjs
USER node
