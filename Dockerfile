FROM node:24-trixie-slim@sha256:c83040f7e24bacea68e58a0b96a484ba430bf24abb2973eab7ba4701144b7b63 AS webui-builder

WORKDIR /app
COPY webui/package.json webui/package-lock.json ./webui/
WORKDIR /app/webui
RUN npm ci
COPY webui/ ./
COPY packages/client-events/ /app/packages/client-events/
RUN mkdir -p /app/nanobot/web && npm run build

# The Python 3.12 toolchain (uv plus the standalone interpreter) is carried
# over from the pinned uv image. Both build and runtime use Debian Trixie,
# the current Debian stable release; the runtime remains the slim variant.
FROM ghcr.io/astral-sh/uv:0.9.30-python3.12-trixie-slim@sha256:41eb228142f776ed8df9e51fba89ee31f018c04a0452645c014783546b164c03 AS toolchain

FROM debian:trixie-slim@sha256:f6b08b09a05725f9431502d3b5714f5c4576e82c1a84fa1debe0c24a7e0c3ec4 AS openssh-builder
ARG DEBIAN_SNAPSHOT=20261030T000000Z
ARG OPENSSH_VERSION=10.6p1
ARG OPENSSH_SHA256=a9dc9565dffe8640f64d863cd29a32bc4a3dbdec0566a7fc44c5d6ee767d5f39
RUN printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s trixie main\n' "$DEBIAN_SNAPSHOT" > /etc/apt/sources.list && \
    printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/%s trixie-security main\n' "$DEBIAN_SNAPSHOT" >> /etc/apt/sources.list && \
    rm -f /etc/apt/sources.list.d/debian.sources && \
    apt-get -o Acquire::Check-Valid-Until=false update && \
    apt-get install -y --no-install-recommends build-essential ca-certificates curl \
        libedit-dev libkrb5-dev libssl-dev pkg-config zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*
RUN curl -fsSLo /tmp/openssh.tar.gz \
        "https://cdn.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-${OPENSSH_VERSION}.tar.gz" && \
    printf '%s  %s\n' "$OPENSSH_SHA256" /tmp/openssh.tar.gz | sha256sum -c - && \
    mkdir -p /tmp/openssh-src && \
    tar -xzf /tmp/openssh.tar.gz --strip-components=1 -C /tmp/openssh-src && \
    cd /tmp/openssh-src && \
    ./configure --prefix=/usr --sysconfdir=/etc/ssh --with-privsep-path=/var/empty \
        --without-pam --without-selinux && \
    make -j2 && \
    make install-nokeys DESTDIR=/tmp/openssh-stage
RUN set -eu; \
    pkg=/tmp/openssh-package; \
    mkdir -p "$pkg/DEBIAN" "$pkg/usr/share/doc/openssh-client"; \
    for program in ssh scp ssh-add ssh-agent ssh-keygen ssh-keyscan sftp; do \
        install -D -m 0755 "/tmp/openssh-stage/usr/bin/$program" "$pkg/usr/bin/$program"; \
    done; \
    install -D -m 0644 /tmp/openssh-stage/etc/ssh/ssh_config "$pkg/etc/ssh/ssh_config"; \
    for page in ssh.1 scp.1 ssh-add.1 ssh-agent.1 ssh-keygen.1 ssh-keyscan.1 sftp.1; do \
        install -D -m 0644 "/tmp/openssh-stage/usr/share/man/man1/$page" "$pkg/usr/share/man/man1/$page"; \
    done; \
    install -m 0644 /tmp/openssh-src/LICENCE "$pkg/usr/share/doc/openssh-client/copyright"; \
    printf 'OpenSSH Portable %s\nSource: https://cdn.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-%s.tar.gz\nSHA-256: %s\n' \
        "$OPENSSH_VERSION" "$OPENSSH_VERSION" "$OPENSSH_SHA256" > "$pkg/usr/share/doc/openssh-client/BUILD-INFO"; \
    printf 'Package: openssh-client\nSource: openssh (10.6p1)\nVersion: 1:10.6p1-1+local1\nArchitecture: amd64\nMaintainer: Positronic Bean Labs\nDepends: libc6 (>= 2.34), libedit2, libgssapi-krb5-2, libkrb5-3, libssl3t64, zlib1g\nDescription: OpenSSH client tools built from upstream 10.6p1 for Debian Trixie\n' \
        > "$pkg/DEBIAN/control"; \
    dpkg-deb --build --root-owner-group "$pkg" /tmp/openssh-client.deb

FROM debian:trixie-slim@sha256:f6b08b09a05725f9431502d3b5714f5c4576e82c1a84fa1debe0c24a7e0c3ec4 AS runtime

COPY --from=toolchain /usr/local/bin/uv /usr/local/bin/uv
COPY --from=toolchain /usr/local/bin/python3.12 /usr/local/bin/python3.12
COPY --from=toolchain /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=toolchain /usr/local/lib/libpython3.12.so.1.0 /usr/local/lib/libpython3.12.so.1.0
# The carried-over interpreter ships pip 25.0.1, whose own vendored SBOM makes
# Trivy report msgpack, setuptools and urllib3 as installed packages of this
# image. Those components are not reachable at runtime, so the report is a
# scanner artifact rather than a finding; dropping pip removes the artifact at
# its source instead of waiving it. uv is the supported installer here and
# `optional_features.install_extra` already falls back to it when pip is absent.
# The ensurepip wheel is removed with it so the image cannot reintroduce the
# vulnerable pip through the last-resort bootstrap.
RUN ln -sf /usr/local/lib/libpython3.12.so.1.0 /usr/local/lib/libpython3.12.so && \
    ln -sf /usr/local/bin/python3.12 /usr/local/bin/python3 && \
    ln -sf /usr/local/bin/python3.12 /usr/local/bin/python && \
    rm -rf /usr/local/lib/python3.12/site-packages/pip /usr/local/lib/python3.12/site-packages/pip-*.dist-info \
           /usr/local/lib/python3.12/ensurepip/_bundled

ARG VERSION=0.1.0
ARG GIT_SHA=unknown
ARG OPENSSH_VERSION=10.6p1
ARG OPENSSH_SHA256=a9dc9565dffe8640f64d863cd29a32bc4a3dbdec0566a7fc44c5d6ee767d5f39
LABEL org.opencontainers.image.title="Percival Gateway" \
      org.opencontainers.image.description="Percival Python gateway and WebUI" \
      org.opencontainers.image.source="https://github.com/bill-kopp-ai-dev/nanobot" \
      org.opencontainers.image.documentation="https://github.com/bill-kopp-ai-dev/nanobot/blob/main/README.md" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="Positronic Bean Labs" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${GIT_SHA}" \
      io.percival.openssh.version="${OPENSSH_VERSION}" \
      io.percival.openssh.source.sha256="${OPENSSH_SHA256}"

ARG DEBIAN_SNAPSHOT=20261030T000000Z
# The slim base has no CA bundle yet; APT still verifies the signed Release
# metadata and package hashes while fetching the pinned snapshot over HTTP.
RUN --mount=type=bind,from=openssh-builder,source=/tmp/openssh-client.deb,target=/tmp/openssh-client.deb,ro \
    printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s trixie main\n' "$DEBIAN_SNAPSHOT" > /etc/apt/sources.list && \
    printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/%s trixie-security main\n' "$DEBIAN_SNAPSHOT" >> /etc/apt/sources.list && \
    rm -f /etc/apt/sources.list.d/debian.sources && \
    apt-get -o Acquire::Check-Valid-Until=false update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get install -y --no-install-recommends \
        ca-certificates git bubblewrap libmagic1 \
        libffi8 libsqlite3-0 libreadline8 libncursesw6 libtinfo6 \
        libdb5.3 libgdbm6 libbz2-1.0 liblzma5 libuuid1 libzstd1 zlib1g && \
    dpkg -i /tmp/openssh-client.deb && \
    chmod u-s /usr/bin/mount && \
    rm -f /usr/bin/nsenter /usr/bin/infocmp && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Keep the environment layout compatible with UID 1000 and alternate UIDs.
# Channel dependencies are installed at build time, not at startup.
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
# The venv is created without `--seed`: a seeded pip brings its own vendored
# SBOM, which the scanner reads as installed msgpack, setuptools and urllib3
# packages of this image. uv installs the locked dependencies and is the
# installer `optional_features.install_extra` uses when pip is absent.
RUN uv venv "$VIRTUAL_ENV"

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
RUN python -m scripts.install_channel_dependencies --locked $(printf '%s' "$NANOBOT_CHANNELS" | tr ',' ' ') && \
    uv pip check --python /app/.venv/bin/python

# Render deploy template (see render.yaml): committed gateway config that wires
# secrets through ${ANTHROPIC_API_KEY} / ${NANOBOT_WEB_TOKEN} env vars (resolved
# at startup). Lives in the code dir (/app), not the data dir, so a mounted disk
# won't shadow it. Only used when RENDER=true; ignored by local runs.
COPY render-config.json ./

# Create the non-root user and hand ownership of the writable virtualenv to it.
RUN useradd -m -u 1000 -s /bin/bash nanobot && \
    mkdir -p /home/nanobot/.nanobot && \
    chmod 755 /home/nanobot && \
    chmod -R a+rX /app/nanobot /app/scripts /app/channel-locks /app/.venv && \
    chmod a+r /app/pyproject.toml /app/uv.lock && \
    chown -R nanobot:nanobot /home/nanobot /app/.venv

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
# `a+rx` (not just `+x`) keeps the script readable by the non-root UID that
# Compose pins in docker-compose.yml; with only `+x` the shell interpreter
# cannot open a 711 file owned by root, and the container restarts in a loop.
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod a+rx /usr/local/bin/entrypoint.sh

# Start as root so the entrypoint can chown the data dir (on Render, the
# freshly-mounted root-owned persistent disk) before dropping to the non-root
# nanobot user via setpriv. The entrypoint drops privileges on every root start
# and fails closed if it cannot, so the agent never runs as root (see
# entrypoint.sh).
USER root
ENV HOME=/home/nanobot
ENV NANOBOT_CHANNEL_LOCK_DIR=/app/channel-locks
# Native Python retains optional installs. Docker candidates require all enabled
# channels/extras in the reviewed build; neither startup nor WebUI installs them.
ENV NANOBOT_RUNTIME_PACKAGE_INSTALL=0
# Ensure crash output reaches Render logs (app output is otherwise swallowed on
# non-graceful exit).
ENV PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1

# Gateway health endpoint and optional WebUI/WebSocket channel ports
EXPOSE 18790 8765

ENTRYPOINT ["entrypoint.sh"]
STOPSIGNAL SIGTERM
CMD ["status"]
