# statute-twins / Apertus-Recht evaluation image. CPU only; no model weights in the image.
#   default target: steps 1-2 of `make run` (no model) and the API live slice (LLM_* variables)
#   target "gguf":  adds llama-cpp-python (prebuilt CPU wheel) for the GGUF live slice
FROM python:3.12.7-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps . && pip install "pyyaml==6.0.2"
COPY statutes ./statutes
COPY dataset ./dataset
COPY results ./results
COPY tests ./tests
ENTRYPOINT ["statute-twins"]
CMD ["selfcheck"]

FROM base AS gguf
RUN pip install "numpy==2.1.3" "jinja2==3.1.4" "huggingface_hub==0.26.2" && \
    pip install "llama-cpp-python==0.3.19" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
