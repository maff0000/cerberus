# CERBERUS WO-1.4 — the DEV live-view image: collector loop + GUI in one image, two services.
#
# NOT one of the six designed images (deploy/Dockerfile.*), which are lifecycle skeletons with no
# work to do and no HTTP surface. This is the smallest honest thing that shows real data: the
# WO-1.2b ingestion runner and the WO-1.3 wiring, behind a plain read-only page.
#
# The base is passed in as a DIGEST reference (CD_PYTHON_BASE), never a tag: same rule as the
# designed images (deploy/base-images.json).
ARG CD_PYTHON_BASE
FROM ${CD_PYTHON_BASE}

ARG CD_BUILD_SHA=unknown
LABEL org.opencontainers.image.title="cd-live-dev" \
      org.opencontainers.image.description="CERBERUS DEV live view: ingestion loop + read-only GUI" \
      org.opencontainers.image.revision="${CD_BUILD_SHA}"

# PyYAML 6.0.2 (not the 6.0 in requirements.txt: 6.0 has no wheel for current interpreters);
# jsonschema pinned to the project's version.
RUN pip install --no-cache-dir PyYAML==6.0.2 jsonschema==4.10.3

RUN groupadd --system --gid 10010 cd-live \
 && useradd --system --uid 10010 --gid 10010 --no-create-home --shell /usr/sbin/nologin cd-live \
 && mkdir /data && chown 10010:10010 /data

WORKDIR /app
COPY --chmod=0555 crash-detector/src/ /app/src/
COPY --chmod=0555 crash-detector/ingestion/ /app/ingestion/
COPY --chmod=0555 crash-detector/gui/ /app/gui/
COPY --chmod=0555 crash-detector/governance/mapping/ /app/governance/mapping/
COPY --chmod=0444 crash-detector/deploy/indicator-scaling.json /app/deploy/indicator-scaling.json
COPY --chmod=0555 crash-detector/deploy/live-dev/collector_loop.py /app/collector_loop.py

ENV PYTHONPATH=/app/src:/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CD_DB_PATH=/data/ingestion.sqlite \
    CD_BUILD_SHA=${CD_BUILD_SHA}

VOLUME ["/data"]
USER 10010:10010
STOPSIGNAL SIGTERM
CMD ["python3", "-B", "/app/gui/server.py"]
