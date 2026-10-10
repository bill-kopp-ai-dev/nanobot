FROM node:24-trixie-slim@sha256:c83040f7e24bacea68e58a0b96a484ba430bf24abb2973eab7ba4701144b7b63 AS webui-builder

WORKDIR /app
COPY webui/package.json webui/package-lock.json ./webui/
WORKDIR /app/webui
RUN npm ci
COPY webui/ ./
COPY packages/client-events/ /app/packages/client-events/
RUN mkdir -p /app/nanobot/web && npm run build

FROM ghcr.io/astral-sh/uv:0.9.30-python3.12-trixie-slim@sha256:eacce4ec0ff855c8be0cca407d8c5e8e20139dd3f8f64c018fb654bac0a40bd8 AS runtime

ARG VERSION=0.3.5
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.title="Percival Gateway" \
      org.opencontainers.image.description="Percival Python gateway and WebUI" \
      org.opencontainers.image.source="https://github.com/bill-kopp-ai-dev/nanobot" \
      org.opencontainers.image.documentation="https://github.com/bill-kopp-ai-dev/nanobot/blob/main/README.md" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="Positronic Bean Labs" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${GIT_SHA}"

ARG DEBIAN_SNAPSHOT=20261009T000000Z
RUN printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s trixie main\n' "$DEBIAN_SNAPSHOT" > /etc/apt/sources.list && \
    printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/%s trixie-security main\n' "$DEBIAN_SNAPSHOT" >> /etc/apt/sources.list && \
    rm -f /etc/apt/sources.list.d/debian.sources && \
    apt-get -o Acquire::Check-Valid-Until=false update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get install -y --no-install-recommends \
        ca-certificates=20250419 git=1:2.47.3-0+deb13u1 \
        bubblewrap=0.12.0-1~deb13u1 openssh-client=1:10.0p1-7+deb13u4 \
        libmagic1t64=1:5.46-5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Keep the runtime environment writable by the non-root nanobot user. Enabled
# channels may install their manifest-declared dependencies at startup.
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN uv venv --seed "$VIRTUAL_ENV"

# Install Python dependencies from the checked-in lock first (cached layer).
# The project itself is deferred until its custom build-hook inputs are present.
ARG NANOBOT_EXTRAS=
COPY pyproject.toml uv.lock README.md LICENSE THIRD_PARTY_NOTICES.md hatch_build.py ./
# The build hook validates the reviewed KG core and SPA snapshots even during
# the dependency-only install. They must exist before uv pip install . runs.
COPY nanobot/agent/kg/vendor/ nanobot/agent/kg/vendor/
COPY nanobot/web/kg-interface/ nanobot/web/kg-interface/
COPY nanobot/__init__.py nanobot/optional_features.py nanobot/
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN if [ -n "$NANOBOT_EXTRAS" ]; then \
        uv sync --locked --no-dev --no-install-project --extra "$NANOBOT_EXTRAS"; \
    else \
        uv sync --locked --no-dev --no-install-project; \
    fi

# Copy the full source and install
COPY nanobot/ nanobot/
COPY scripts/compile_channel_locks.py scripts/install_channel_dependencies.py scripts/
COPY channel-locks/ /app/channel-locks/
COPY --from=webui-builder /app/nanobot/web/dist/ nanobot/web/dist/
RUN if [ -n "$NANOBOT_EXTRAS" ]; then \
        uv sync --locked --no-dev --no-editable --extra "$NANOBOT_EXTRAS"; \
    else \
        uv sync --locked --no-dev --no-editable; \
    fi
RUN python -m scripts.compile_channel_locks --check

# Preinstall selected channel dependencies from their manifests. A comma-separated
# list keeps the image configurable while preserving WhatsApp in the default image.
ARG NANOBOT_CHANNELS=whatsapp
RUN for channel in $(printf '%s' "$NANOBOT_CHANNELS" | tr ',' ' '); do \
        python -m scripts.install_channel_dependencies "$channel"; \
    done

# Render deploy template (see render.yaml): committed gateway config that wires
# secrets through ${ANTHROPIC_API_KEY} / ${NANOBOT_WEB_TOKEN} env vars (resolved
# at startup). Lives in the code dir (/app), not the data dir, so a mounted disk
# won't shadow it. Only used when RENDER=true; ignored by local runs.
COPY render-config.json ./

# Create the non-root user and hand ownership of the writable virtualenv to it.
RUN useradd -m -u 1000 -s /bin/bash nanobot && \
    mkdir -p /home/nanobot/.nanobot && \
    chown -R nanobot:nanobot /home/nanobot /app/.venv

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

# Start as root so the entrypoint can chown the data dir (on Render, the
# freshly-mounted root-owned persistent disk) before dropping to the non-root
# nanobot user via setpriv. The entrypoint drops privileges on every root start
# and fails closed if it cannot, so the agent never runs as root (see
# entrypoint.sh).
USER root
ENV HOME=/home/nanobot
ENV NANOBOT_CHANNEL_LOCK_DIR=/app/channel-locks
# Ensure crash output reaches Render logs (app output is otherwise swallowed on
# non-graceful exit).
ENV PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1

# Gateway health endpoint and optional WebUI/WebSocket channel ports
EXPOSE 18790 8765

ENTRYPOINT ["entrypoint.sh"]
CMD ["status"]
