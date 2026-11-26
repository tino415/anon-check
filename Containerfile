FROM docker.io/library/python:3.12-slim AS base
ARG LIBRARY=gliner
ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install "$LIBRARY"
RUN useradd --create-home --uid 1000 anon
ENV HF_HOME=/opt/hf PYTHONPATH=/opt/anon-check/src
WORKDIR /opt/anon-check
COPY src src

FROM base AS test
RUN pip install pytest
COPY pyproject.toml ./
COPY tests tests
COPY eval eval
ENV ANON_CHECK_MODEL=none HF_HUB_OFFLINE=1
USER anon
ENTRYPOINT ["python", "-m", "pytest", "-p", "no:cacheprovider"]

FROM base AS app
ARG LIBRARY=gliner
ARG MODEL=none
ARG THRESHOLD=0.5
ENV ANON_CHECK_MODEL=${LIBRARY}:${MODEL} ANON_CHECK_THRESHOLD=${THRESHOLD}
RUN python -m anon_check.warm_up
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
LABEL anon-check=keep
USER anon
ENTRYPOINT ["python", "-m", "anon_check"]

FROM app AS eval
COPY eval eval
ENTRYPOINT ["python", "eval/recall.py"]
