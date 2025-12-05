FROM debian:13-slim AS exporter

RUN apt-get update \
    && apt-get -y --no-install-recommends install \
       sudo curl git ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV MISE_DATA_DIR="/mise"
ENV MISE_CONFIG_DIR="/mise"
ENV MISE_CACHE_DIR="/mise/cache"
ENV MISE_INSTALL_PATH="/usr/local/bin/mise"
ENV PATH="/mise/shims:$PATH"

COPY mise.toml ./
RUN curl https://mise.run | sh && \
    mise trust && \
    mise i

WORKDIR /opt/app/
COPY pyproject.toml uv.lock ./
RUN uv export -o requirements.txt --no-default-groups --no-hashes --no-annotate --frozen --no-emit-project

######################################################################
FROM python:3.14-slim-trixie

ENV PYTHONPATH=/opt/app/src
WORKDIR /opt/app/

RUN groupadd app_user \
    && useradd --gid app_user --shell /bin/bash --create-home app_user

COPY --from=exporter /opt/app/pyproject.toml /opt/app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    find /usr/local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local -type f -name "*.pyc" -delete 2>/dev/null || true && \
    rm -rf /root/.cache /tmp/*

COPY src/ /opt/app/src

USER app_user

ENTRYPOINT ["python", "/opt/app/src/alert_manager/cli.py"]
