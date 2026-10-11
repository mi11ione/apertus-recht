# statute-twins / Apertus-Recht evaluation image. CPU only; no model weights in the image.
#   default target: steps 1-2 of `make run` (no model) and the API live slice (LLM_* variables)
#   target "gguf":  adds llama-cpp-python (built from source, portable AVX2) for the GGUF live slice
FROM python:3.12.7-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps . && pip install "pyyaml==6.0.2" "numpy==2.1.3"
COPY statutes ./statutes
COPY dataset ./dataset
COPY results ./results
COPY reports ./reports
COPY prereg ./prereg
COPY scripts ./scripts
COPY runs_a22 ./runs_a22
COPY claims.tsv README.md technical_report.md ./
COPY tests ./tests
ENTRYPOINT ["statute-twins"]
CMD ["selfcheck"]

FROM python:3.12.7 AS llama-build
# llama-cpp-python 0.3.19 vendors a 2026 llama.cpp that supports the Apertus architecture; built from source because
# its prebuilt CPU wheels are musl-linked. Portable AVX2 build (no -march=native), a few minutes on a laptop.
ENV CMAKE_ARGS="-DGGML_NATIVE=OFF -DGGML_AVX=ON -DGGML_AVX2=ON -DGGML_FMA=ON -DGGML_F16C=ON"
RUN pip wheel --no-deps -w /wheels "llama-cpp-python==0.3.19"

FROM base AS gguf
COPY --from=llama-build /wheels /wheels
RUN pip install "numpy==2.1.3" "jinja2==3.1.4" "huggingface_hub==0.26.2" "diskcache==5.6.3" "typing-extensions" && \
    pip install --no-deps /wheels/llama_cpp_python-0.3.19-*.whl
