# Quickstart

```bash
cd track_1b
make run                       # Docker, CPU: dataset regenerates from the statute YAML; results recompute from responses
LLM_NAME=... LLM_BASE_URL=... LLM_API_KEY=... make run      # + live slice on your endpoint (any OpenAI-compatible API)
make run-gguf                  # + live slice on the public Q4_K_M GGUF of Apertus v1.5 8B (5.1 GB download, CPU)
make test                      # the test suite inside the image
```

Without Docker (Python ≥ 3.10; on macOS the system `python3` is 3.9, so name the version):

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/statute-twins selfcheck && .venv/bin/python -m pytest -q
```

## Score your own model

```bash
export LLM_BASE_URL=http://localhost:8000/v1 LLM_NAME=my-model LLM_API_KEY=...
statute-twins eval --run-id my-model --parts core_de --rungs R0,R3,R4 --sample 240   # ~240 items, whole twin groups
statute-twins report --run runs/my-model.jsonl                                      # Markdown + HTML page
```

`eval` writes `runs/<run-id>.jsonl` (never the released dataset), prints how many prompts were decided, unparsed or
errored, and exits 1 if any were (`--max-error-rate` to tolerate some). Re-running the same command retries only the
missing prompts. `report` gives one page: accuracy with intervals, the element read-back (which legal element the
model applies against the statute), and every wrong decision with its scenario, gold verdict, derivation and sources.
For all models at once: `statute-twins results --responses runs --out runs/results.json` (add `--dataset` if your
prompts come from another dataset folder; a run that matches no item is reported, not silently empty).

Free text (the track's second metric): generate with `--framings open --mode generate`, then
`statute-twins judge packets --run my-model --work jw`, `statute-twins judge judge --who A --work jw` (and `--who B`;
any OpenAI-compatible judge model via `LLM_*`), `statute-twins judge aggregate --run my-model --work jw`. The aggregate
reports the judges' agreement and checks their reading against a deterministic parser on every settled answer.

`eval` checks the endpoint with one request before the run and stops with the error if it is missing or unreachable.
Sample size: the read-back needs at least 5 pairs per element and rung to be readable; `--sample 240` gives that for
most elements of the German core set, the full set (660 items) for all. Rows with fewer pairs say "too few pairs".
