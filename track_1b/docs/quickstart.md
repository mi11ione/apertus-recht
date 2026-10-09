# Quickstart

```bash
cd track_1b
make run                       # Docker, CPU: dataset regenerates from the statute YAML; results recompute from responses
LLM_NAME=... LLM_BASE_URL=... LLM_API_KEY=... make run      # + live slice on your endpoint (any OpenAI-compatible API)
make run-gguf                  # + live slice on the public Q4_K_M GGUF of Apertus v1.5 8B (5.1 GB download, CPU)
make test                      # the test suite inside the image
```

Without Docker (Python ≥ 3.10): `pip install -e ".[dev]" && statute-twins selfcheck && python -m pytest -q`.

Score a new model on the full set: `statute-twins eval --backend openai --run-id <name> --parts core_de,core_fr,core_it
--rungs R0,R3,R4`, then `statute-twins results` writes `results/results.json`, and `statute-twins selfcheck` verifies it.
