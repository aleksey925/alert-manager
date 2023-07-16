FROM python:3.11-slim-buster

ENV PDM_VERSION=2.7.4
WORKDIR /opt/app/

RUN pip install pdm==$PDM_VERSION
COPY pyproject.toml pdm.lock /opt/app/
RUN pdm export --prod --without-hashes -o requirements.txt

######################################################################
FROM python:3.11-slim-buster

ENV PYTHONPATH=/opt/app/src
WORKDIR /opt/app/

RUN groupadd app_user \
    && useradd --gid app_user --shell /bin/bash --create-home app_user

COPY --from=0 /opt/app/pyproject.toml /opt/app/requirements.txt ./
RUN pip install -r requirements.txt \
    && rm -rf /root/.cache/pip

COPY src/ /opt/app/src

USER app_user

ENTRYPOINT ["python", "/opt/app/src/alert_manager/cli.py"]
