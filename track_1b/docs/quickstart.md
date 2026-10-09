# Quickstart

```bash
cd track_1b
make run                       # Docker, CPU: dataset regenerates from the statute YAML; results recompute from responses
LLM_NAME=... LLM_BASE_URL=... LLM_API_KEY=... make run      # + live slice on your endpoint (any OpenAI-compatible API)
make run-gguf                  # + live slice on the public Q4_K_M GGUF of Apertus v1.5 8B (5.1 GB download, CPU)
make test                      # the test suite inside the image
```

Without Docker (Python ≥ 3.10): `pip install -e ".[dev]" && statute-twins selfcheck && python -m pytest -q`.

## Score your own model

```bash
export LLM_BASE_URL=http://localhost:8000/v1 LLM_NAME=my-model LLM_API_KEY=...
statute-twins eval --run-id my-model --parts core_de --rungs R0,R3,R4 --sample 120   # ~120 items, whole twin groups
statute-twins report --run runs/my-model.jsonl                                      # Markdown + HTML page
```

`eval` writes `runs/<run-id>.jsonl` (never the released dataset), prints how many prompts were decided, unparsed or
errored, and exits 1 if any were (`--max-error-rate` to tolerate some). Re-running the same command retries only the
missing prompts. `report` gives one page: accuracy with intervals, the element read-back (which legal element the
model applies against the statute), and every wrong decision with its scenario, gold verdict, derivation and sources.
For all models at once: `statute-twins results --responses runs --out runs/results.json`.
