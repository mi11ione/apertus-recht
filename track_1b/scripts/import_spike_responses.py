"""Import the cached exploration-spike scores into the harness response format (development only; needs the spike
folder, which is not part of the repository). Run once; the output files in dataset/responses/ are what `make run`
re-scores.

    python scripts/import_spike_responses.py ~/Desktop/hackapertus/spikes dataset/responses

Every row keeps the source file and its sha256, so each imported number can be traced to the measurement that made it.
Builds and their labels (see docs/builds.md for the evidence behind each label):
  8b-bf16-{RLVR,DPO}     swiss-ai/Apertus-v1.5-8B-{RLVR,DPO}, bf16, MLX, chat template      linie9/results/stage_bf16_*.json
  8b-mlx4-{SFT,RLVR,DPO,final}  same stages, MLX 4-bit g64 conversion, chat template      linie9/results/stage_*.json
  8b-mlx4-base-completion  base checkpoint, MLX 4-bit g64, template-free completion        linie9/results/stage_base.json
  8b-gguf-q8_0 / q4_k_m  the two public GGUFs of v1.5 8B (final), llama.cpp, chat template  gguf/stage_gguf_q*.json
  publicai-70b-fc        Public AI name swiss-ai/apertus-v1.5-8b, which serves the 70B          live/results/fc_apertus-v1.5-8b.json
                         (spikes/live/results.md), exact forced choice via prefill + prompt_logprobs
  publicai-70b-gen       Public AI name swiss-ai/apertus-v1.5-70b (fp1-nes), free generation      live/results/gen_apertus-v1.5-70b.json
  qwen3-8b-mlx4          mlx-community/Qwen3-8B-4bit, comparator (not Apertus)                 linie9/results/qwen.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from statute_twins.generator import design, legacy  # noqa: E402

LEGACY_SET = {"ladder": "ladder", "never": "never"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pid(set_name: str, item: str, variant: str, rung: str, framing: str) -> str:
    return f"{legacy.legacy_id(set_name, dict(item=item, variant=variant))}/{rung}/{framing}"


def write(out: Path, run: str, rows: list[dict], meta: dict) -> None:
    rows = sorted(rows, key=lambda r: r["prompt_id"])
    p = out / f"{run}.jsonl"
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    meta = dict(run=run, rows=len(rows), jsonl_sha256=sha(p), **meta)
    (out / f"{run}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{run}: {len(rows)} rows")


def stage9(spikes: Path, out: Path, src: str, run: str, label: dict, arm: str = "chat") -> None:
    f = spikes / src
    d = json.loads(f.read_text())
    rows = []
    for set_name, items in d["sets"].items():
        for x in items:
            for fr in ("conv", "ver"):
                for r in ("R0", "R3"):
                    c = x.get(f"{arm}_{fr}_{r}")
                    if c is None:
                        continue
                    rows.append(dict(prompt_id=pid(set_name, x["item"], x["variant"], r, fr),
                                     item_id=legacy.legacy_id(set_name, x), lang="de", rung=r, framing=fr, run=run,
                                     method=f"mlx_{arm}" if "gguf" not in run else "llamacpp_chat",
                                     lp_convict=c["lp_yes"], lp_acquit=c["lp_no"], lo_conv=c["lo_conv"],
                                     decision="convict" if c["lo_conv"] > 0 else "acquit",
                                     extra=dict(mass=c.get("mass"), ntok=c.get("ntok")),
                                     source=dict(file=f"spikes/{src}", sha256=sha(f))))
    write(out, run, rows, dict(label, protocol=arm, source_file=f"spikes/{src}", source_sha256=sha(f),
                               questions_note="stage9.py question strings, byte-identical to prompts/de.yaml R0/R3"))


def live_fc(spikes: Path, out: Path) -> None:
    src = "live/results/fc_apertus-v1.5-8b.json"
    f = spikes / src
    d = json.loads(f.read_text())
    rows = []
    for x in d["rows"]:
        if "error" in x:
            continue
        fr, r = x["cell"].split("_")
        calls = list(x["calls"].values())
        rows.append(dict(prompt_id=pid(x["set"], x["item"], x["variant"], r, fr),
                         item_id=legacy.legacy_id(x["set"], x), lang="de", rung=r, framing=fr, run="publicai-70b-fc",
                         method="exact_prefill", served_model=calls[0]["model"], fingerprint=calls[0]["fp"],
                         lp_convict=x["lp_yes"], lp_acquit=x["lp_no"], lo_conv=x["lo_conv"],
                         decision="convict" if x["lo_conv"] > 0 else "acquit",
                         source=dict(file=f"spikes/{src}", sha256=sha(f))))
    write(out, "publicai-70b-fc", rows, dict(
        model="Apertus v1.5 70B as served by Public AI under the name swiss-ai/apertus-v1.5-8b",
        requested_model="swiss-ai/apertus-v1.5-8b", size_evidence="spikes/live/results.md: same weights as the -70b name "
        "(760/792 byte-identical greedy outputs); MMLU 84.4% vs 70.8% for the v1 8B route; tp8-pp2 deployment",
        protocol="exact forced choice: candidate prefilled as assistant turn, prompt_logprobs summed (live.py fc)",
        temperature=0, source_file=f"spikes/{src}", source_sha256=sha(f)))


def live_gen(spikes: Path, out: Path) -> None:
    src = "live/results/gen_apertus-v1.5-70b.json"
    f = spikes / src
    d = json.loads(f.read_text())
    rows = []
    for x in d["rows"]:
        if "error" in x:
            continue
        fr, r = x["cell"].split("_")
        dec = {1: "convict", 0: "acquit", None: "unparsed"}[x["dec"]]
        rows.append(dict(prompt_id=pid(x["set"], x["item"], x["variant"], r, fr),
                         item_id=legacy.legacy_id(x["set"], x), lang="de", rung=r, framing=fr, run="publicai-70b-gen",
                         method="generate", served_model=x["model"], fingerprint=x["fp"], lp_convict=None, lp_acquit=None,
                         lo_conv=None, decision=dec, text=x["text"],
                         source=dict(file=f"spikes/{src}", sha256=sha(f))))
    write(out, "publicai-70b-gen", rows, dict(
        model="Apertus v1.5 70B (Public AI name swiss-ai/apertus-v1.5-70b, backend fp1-nes)",
        requested_model="swiss-ai/apertus-v1.5-70b", protocol="plain user message, greedy, 24 tokens, decision parsed",
        source_file=f"spikes/{src}", source_sha256=sha(f)))


def qwen(spikes: Path, out: Path) -> None:
    src = "linie9/results/qwen.json"
    f = spikes / src
    d = json.loads(f.read_text())
    rows = []
    for set_name, items in d["sets"].items():
        for x in items:
            for fr in ("conv", "ver"):
                for r in ("R0", "R2", "R3", "R4"):
                    c = x.get(f"{fr}_{r}")
                    if c is None:
                        continue
                    lpc, lpa = c.get("lp_ja", c.get("lp_yes")), c.get("lp_nein", c.get("lp_no"))
                    rows.append(dict(prompt_id=pid(set_name, x["item"], x["variant"], r, fr),
                                     item_id=legacy.legacy_id(set_name, x), lang="de", rung=r, framing=fr,
                                     run="qwen3-8b-mlx4", method="mlx_chat", lp_convict=lpc, lp_acquit=lpa,
                                     lo_conv=c["lo_conv"], decision="convict" if c["lo_conv"] > 0 else "acquit",
                                     extra=dict(mass=c.get("mass")), source=dict(file=f"spikes/{src}", sha256=sha(f))))
    write(out, "qwen3-8b-mlx4", rows, dict(model=d["model"], comparator=True, protocol="spike9.py chat forced choice",
                                           source_file=f"spikes/{src}", source_sha256=sha(f)))


def main(spikes: str, out: str) -> None:
    spikes, out = Path(spikes).expanduser(), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    d = design.load(ROOT / "statutes/stgb_261bis", langs=["de"])
    q = json.loads((spikes / "linie9/results/stage_bf16_DPO.json").read_text())["meta"]["questions"]
    from statute_twins.generator.render import question
    for fr in ("conv", "ver"):
        for r in ("R0", "R3"):
            assert question(d, "de", r, fr) == q[fr][r]
    B = "swiss-ai/Apertus-v1.5-8B"
    for stage in ("RLVR", "DPO"):
        stage9(spikes, out, f"linie9/results/stage_bf16_{stage}.json", f"8b-bf16-{stage}",
               dict(model=f"{B}-{stage}", precision="bf16", runtime="MLX 0.32.3 / mlx-lm 0.32.0 (M4, 24 GB)"))
    for stage in ("SFT", "RLVR", "DPO", "final"):
        repo = B if stage == "final" else f"{B}-{stage}"
        stage9(spikes, out, f"linie9/results/stage_{stage}.json", f"8b-mlx4-{stage}",
               dict(model=repo, precision="MLX 4-bit g64 (own conversion)", runtime="mlx-lm 0.32.0 (M2 Air)"))
    stage9(spikes, out, "linie9/results/stage_base.json", "8b-mlx4-base-completion",
           dict(model=f"{B}-base", precision="MLX 4-bit g64", runtime="mlx-lm 0.32.0",
                note="template-free completion (<s> + fact + question + Antwort:/Urteil:); not comparable to chat rows"),
           arm="comp")
    stage9(spikes, out, "gguf/stage_gguf_q8.json", "8b-gguf-q8_0",
           dict(model="andreasmartin/apertus-v1.5-8b-text-Q8_0-GGUF", file="apertus-v1.5-8b-text-q8_0.gguf",
                sha256="dea904ad80cd725ec89962abae464477f5d8114d1f4377514f381f7dc2ed202d", runtime="llama.cpp 0.6.0 (ggml 0.26.0), Metal"))
    stage9(spikes, out, "gguf/stage_gguf_q4.json", "8b-gguf-q4_k_m",
           dict(model="Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF", file="apertus-v1.5-8b-text-q4_k_m.gguf",
                sha256="a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299", runtime="llama.cpp 0.6.0 (ggml 0.26.0), Metal"))
    live_fc(spikes, out)
    live_gen(spikes, out)
    qwen(spikes, out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
