# Model builds behind each response run

Every file in `dataset/responses/` names the build it measured. The labels below are deliberate, and some differ from
the names the providers use.

| run | what it is | evidence |
|---|---|---|
| `8b-bf16-RLVR`, `8b-bf16-DPO` | `swiss-ai/Apertus-v1.5-8B-RLVR` / `-DPO` checkpoints, full bf16 precision, MLX, chat template | exploration runs (imported; the spike notes are not part of the repository); byte-identical question strings (test `test_generator.py`) |
| `8b-mlx4-{SFT,RLVR,DPO,final}` | the same stages after our own MLX 4-bit g64 conversion | imported exploration run; this conversion **distorts verdicts** (548/648 decisions agree with bf16 DPO) and is kept only as evidence of that |
| `8b-mlx4-base-completion` | the base checkpoint, template-free completion | base is agnostic (\|lo\| < 1 everywhere); not comparable to chat rows |
| `8b-gguf-q8_0` | `andreasmartin/apertus-v1.5-8b-text-Q8_0-GGUF`, sha256 `dea904ad…202d`, llama.cpp | 638/648 decisions agree with bf16 DPO, as close as two adjacent training stages |
| `8b-gguf-q4_k_m` | `Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF`, sha256 `a037df8d…f299`, llama.cpp | 622/648 agree with bf16 DPO; the build the harness downloads for `make run-gguf` |
| `publicai-70b-fc`, `publicai-70b-fc-core` | **Apertus v1.5 70B** as served by Public AI under the name `swiss-ai/apertus-v1.5-8b`, exact forced choice | the `-8b` and `-70b` names return byte-identical greedy output in 760/792 cells; 84.4% vs 70.8% on 250 MMLU items against Public AI's v1 8B route; 16-GPU tp8-pp2 deployment; 21–28 vs 93 tok/s. Every row records the served `model` field and backend fingerprint |
| `publicai-70b-gen` | the same 70B under the name `swiss-ai/apertus-v1.5-70b` (backend `fp1-nes`), free generation, decision parsed | no logprobs on this name; a system message or assistant prefill there is silently answered by `Qwen-SEA-LION-v4-32B-IT`, so only plain user messages are sent and the served model is checked on every call |
| `qwen3-8b-mlx4` | `mlx-community/Qwen3-8B-4bit`, comparator (not Apertus) | its verdict-word continuations carry ~1e-7 probability, so its `ver` rows are weak evidence |

Public AI may route requests outside Switzerland; it is a measurement endpoint here, not a deployment recommendation.
The 8B numbers come only from local runs (bf16, GGUF, MLX) and from the CPU runner workflow
(`.github/workflows/gguf-8b.yml`); nothing in this repository treats Public AI's `-8b` name as an 8B.
