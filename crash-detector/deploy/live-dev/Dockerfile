# CERBERUS WO-1.4 — the DEV live-view image: collector loop + GUI in one image, two services.
# WO-1.3a adds the evaluator loop: the SAME image, now three services.
#
# NOT one of the six designed images (deploy/Dockerfile.*), which are lifecycle skeletons with no
# work to do and no HTTP surface. This is the smallest honest thing that shows real data: the
# WO-1.2b ingestion runner and the WO-1.3 wiring, behind a plain read-only page.
#
# WO-1.3a ADDS NO DEPENDENCY, NO LAYER OF ITS OWN BEYOND TWO COPIES, AND NO EGRESS. The evaluator
# imports only `crash_detector.*`, `ingestion.*` and the new `evaluator` package — all stdlib-plus-
# this-repo, nothing that is not already pip-installed below for the other two services (checked:
# `evaluator/` imports json, re, sqlite3, dataclasses, datetime, typing and nothing else external).
# The pip line is therefore UNCHANGED, which is the finding spec §11 expected and not a hope.
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
# jsonschema pinned to the project's version; redis pinned to the WO-1.12 version (DEP-REDIS-001).
#
# THIS LINE IS NOT requirements.lock, AND THAT IS A PRE-EXISTING GAP, NOT A WO-1.12 CHOICE: the
# designed install path is the hash-verified lockfile (PBG-CI-003), but this image has always
# pip-installed these pins ad hoc instead. redis now joins PyYAML and jsonschema in that gap.
# Recorded in STATUS.md 4a; fixing the lock pipeline is out of this WO's scope.
#
# redis is needed by BOTH services, not just the collector: ingestion/adapters.py imports redis at
# module scope, and gui/state.py imports ingestion.catalog which imports ingestion.adapters, so the
# GUI will not start without it either. One image, so both get it.
#
# async-timeout is deliberately NOT installed: redis 5.0.1 declares it
# `async-timeout >=4.0.2 ; python_full_version <= "3.11.2"`, and this base image is CPython 3.12.14
# (verified in the running container), so the marker is false here. The DEV HOST is 3.11.2 and does
# need it; the container is not the host.
RUN pip install --no-cache-dir PyYAML==6.0.2 jsonschema==4.10.3 redis==5.0.1

# /state IS CREATED AND CHOWNED HERE FOR THE REASON /data IS: a named volume mounted on a path
# that exists in the image inherits that path's ownership and mode when the volume is first
# initialised, and a volume mounted on a path that does NOT exist arrives root-owned, which uid
# 10010 cannot write. The evaluator's whole job is writing there, so the directory is part of the
# image and not left to the mount.
RUN groupadd --system --gid 10010 cd-live \
 && useradd --system --uid 10010 --gid 10010 --no-create-home --shell /usr/sbin/nologin cd-live \
 && mkdir /data && chown 10010:10010 /data \
 && mkdir /state && chown 10010:10010 /state

WORKDIR /app
COPY --chmod=0555 crash-detector/src/ /app/src/
COPY --chmod=0555 crash-detector/ingestion/ /app/ingestion/
COPY --chmod=0555 crash-detector/gui/ /app/gui/
COPY --chmod=0555 crash-detector/evaluator/ /app/evaluator/
COPY --chmod=0555 crash-detector/governance/mapping/ /app/governance/mapping/
# Create /app/deploy explicitly: COPY --chmod applies to implicitly created parent dirs too, so a
# bare "COPY --chmod=0444 file /app/deploy/" yields a dr--r--r-- dir the non-root user cannot traverse.
RUN mkdir -m 0555 /app/deploy
COPY --chmod=0444 crash-detector/deploy/indicator-scaling.json /app/deploy/indicator-scaling.json
COPY --chmod=0555 crash-detector/deploy/live-dev/collector_loop.py /app/collector_loop.py
COPY --chmod=0555 crash-detector/deploy/live-dev/evaluator_loop.py /app/evaluator_loop.py

ENV PYTHONPATH=/app/src:/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CD_DB_PATH=/data/ingestion.sqlite \
    CD_STATE_PATH=/state/machine_state.sqlite \
    CD_BUILD_SHA=${CD_BUILD_SHA}

# STILL ONLY /data, DELIBERATELY. One image serves three services, and a `VOLUME ["/state"]` here
# would hand the collector and the GUI an ANONYMOUS /state volume each on their next recreate —
# two stray volumes, on two services this round is required not to change. The evaluator's /state
# is a NAMED volume declared on its own service in compose.yaml, which is where a mount that
# belongs to one service of three belongs.
VOLUME ["/data"]
USER 10010:10010
STOPSIGNAL SIGTERM
CMD ["python3", "-B", "/app/gui/server.py"]
