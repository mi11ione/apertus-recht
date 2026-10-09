# Backends: scoring any model

The harness asks every model the same question in two framings and reads its preference between the two verdicts.

| framing | user message ends with | assistant prefix | candidates |
|---|---|---|---|
| `conv` | "… verurteilen? Antworte mit Ja oder Nein." | – | `Ja` / `Nein` |
| `ver` | "… Antworte mit «schuldig» oder «nicht schuldig»." | `Urteil:` | ` schuldig` / ` nicht schuldig` |

(FR: Oui/Non, `Jugement :` coupable/non coupable; IT: Sì/No, `Sentenza:` colpevole/non colpevole.) The score is
`lo = log P(convict continuation) − log P(acquit continuation)`, each summed over all its tokens; `lo > 0` is a
conviction. Rungs R0–R4 add law to the question (R0 none; R1 elements named; R2 + BGE 130 IV 111 publicity rule and the
list; R3 + "the list is closed"; R4 + the 1 July 2020 clause).

## OpenAI-compatible endpoints (`--backend openai`, env `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_NAME`)
- `exact_prefill` (vLLM): the candidate is prefilled as the assistant turn with `continue_final_message=true`,
  `add_generation_prompt=false`, `prompt_logprobs=1`, `max_tokens=1`; the candidate's tokens are read back from the
  prompt log-probabilities and must spell the candidate exactly (otherwise the row errors).
- `top_logprobs`: first-token lookup among the top 20 (framings without a prefix only); censored candidates are flagged.
- `generate`: free generation at temperature 0, decision parsed by a deterministic DE/FR/IT parser.
- `auto` probes once and picks the best supported method. Every response's `model` field must equal the requested model.

## llama.cpp (`--backend llamacpp --gguf PATH`)
In-process llama-cpp-python, CPU. Renders the GGUF's own chat template, decodes the prompt once (reusing the KV cache
for the prefix shared with the previous prompt), teacher-forces each candidate and rewinds. Same protocol as the
spike scorer `llscore.cpp`; tested against a brute-force reference in `tests/test_backends.py`.

## Adding a backend
Subclass `harness.backends.base.Backend`: `describe()` returns everything that identifies the build (it enters the
cache key of every row) and `score(row)` returns a `Score`. Rows are cached by `request_sha256`, so runs resume and
replays verify that the prompts have not changed.

## Examples
```bash
statute-twins eval --backend openai --run-id my-model --parts core_de,core_fr,core_it --rungs R0,R3 --workers 4
statute-twins eval --backend llamacpp --gguf apertus-v1.5-8b-text-q4_k_m.gguf --run-id 8b-q4 --parts core_de --sample 60
statute-twins results && statute-twins selfcheck
```
