"""Step 3 of `make run`: score a small, fixed slice live and check the harness against expected results.

Backends:
  api   any OpenAI-compatible endpoint from LLM_BASE_URL / LLM_API_KEY / LLM_NAME (method picked automatically:
        exact prefill + prompt_logprobs on vLLM, else top-20 logprobs, else generate-and-parse)
  gguf  the public Q4_K_M GGUF of Apertus v1.5 8B, downloaded and sha256-verified, scored on CPU with llama.cpp

Checks (all must pass):
  * every row scored, no served-model mismatch, decisions parse;
  * the harness is deterministic: a second pass over 5 prompts reproduces the first (|Δ lo| <= 1e-3, same decision);
  * if results/reference_bands.json has a band for this backend+model: decision agreement with the published run on
    the same prompts >= min_agreement and mean |Δ lo| <= max_mean_abs_diff.
A model with no band (a new model) passes on the first two checks and its slice results are printed: the harness
accepts new models; the bands only pin the ones we published.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .run import read_jsonl, run as run_rows, stable_sample

GGUF = dict(repo="Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF", file="apertus-v1.5-8b-text-q4_k_m.gguf",
            sha256="a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299")


def slice_rows(ds: Path, n_items: int, rungs=("R0", "R3"), framings=("conv", "ver")) -> list[dict]:
    items = [json.loads(l) for l in (ds / "eval" / "core_de.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    # stratified: the same number of twin groups from every family, whole groups (base + variants)
    fams: dict = {}
    for i in items:
        fams.setdefault(i["family"], set()).add(i["twin_group"])
    per = max(1, n_items // (3 * len(fams)))
    keep = set()
    for f, gs in sorted(fams.items()):
        keep |= {g["prompt_id"] for g in stable_sample([dict(prompt_id=x) for x in sorted(gs)], per, salt="live-slice")}
    want = {i["id"] for i in items if i["twin_group"] in keep}
    prompts = [json.loads(l) for l in (ds / "eval" / "prompts_core_de.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    return [p for p in prompts if p["item_id"] in want and p["rung"] in rungs and p["framing"] in framings]


def _backend(kind: str):
    if kind == "api":
        from .backends.openai_compat import OpenAICompat
        if not os.environ.get("LLM_BASE_URL") or not os.environ.get("LLM_NAME"):
            raise SystemExit("live=api needs LLM_BASE_URL and LLM_NAME (and LLM_API_KEY if the endpoint needs one)")
        be = OpenAICompat(base_url=os.environ["LLM_BASE_URL"], model=os.environ["LLM_NAME"],
                          api_key=os.environ.get("LLM_API_KEY"), mode=os.environ.get("LLM_MODE", "auto"))
        return be, f"api:{os.environ['LLM_NAME']}@{os.environ['LLM_BASE_URL'].rstrip('/')}"
    from huggingface_hub import hf_hub_download
    from .backends.llamacpp import LlamaCpp, sha256_file
    path = hf_hub_download(GGUF["repo"], GGUF["file"], cache_dir=os.environ.get("GGUF_CACHE", "/models"))
    got = sha256_file(path)
    if got != GGUF["sha256"]:
        raise SystemExit(f"GGUF sha256 mismatch: {got}")
    return LlamaCpp(path, expect_sha256=got, label=f"{GGUF['repo']}/{GGUF['file']}"), f"gguf:{GGUF['repo']}"


def run(a) -> bool:
    ds = Path(a.dataset)
    rows = slice_rows(ds, a.live_items)
    be, key = _backend(a.live)
    print(f"  slice: {len(rows)} prompts ({len({r['item_id'] for r in rows})} items) on {key}")
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        st = run_rows(be, rows, tmp, "live", workers=int(os.environ.get("LLM_WORKERS", "2")), progress_every=20)
        got = {r["prompt_id"]: r for r in read_jsonl(Path(tmp) / "live.jsonl")}
        errs = [r for r in got.values() if "error" in r]
        print(f"  scored {len(got) - len(errs)}/{len(rows)}; errors {len(errs)}")
        for e in errs[:5]:
            print("    ", e["prompt_id"], e["error"][:160])
        ok &= not errs and len(got) == len(rows)
        unparsed = [r for r in got.values() if r.get("decision") not in ("convict", "acquit")]
        ok &= not unparsed
        # determinism
        again = rows[:5]
        st2 = run_rows(be, again, tmp, "live_repeat", workers=1, progress_every=0)
        rep = {r["prompt_id"]: r for r in read_jsonl(Path(tmp) / "live_repeat.jsonl")}
        det = bool(rep) and all(p["prompt_id"] in rep and "error" not in rep[p["prompt_id"]] and "error" not in got[p["prompt_id"]]
                                and rep[p["prompt_id"]].get("decision") == got[p["prompt_id"]].get("decision") and
                  (got[p["prompt_id"]].get("lo_conv") is None or abs(rep[p["prompt_id"]]["lo_conv"] - got[p["prompt_id"]]["lo_conv"]) <= 1e-3)
                  for p in again)
        print(f"  determinism (5 prompts re-scored): {'PASS' if det else 'FAIL'}")
        ok &= det
        # accuracy on the slice, for information
        items = {}
        for l in (ds / "eval" / "core_de.jsonl").read_text(encoding="utf-8").splitlines():
            i = json.loads(l)
            items[i["id"]] = i
        cells: dict = {}
        for r in got.values():
            i = items[r["item_id"]]
            if i["label"] != "settled" or r.get("decision") not in ("convict", "acquit"):
                continue
            c = cells.setdefault((r["rung"], r["framing"]), [0, 0])
            c[0] += r["decision"] == i["gold_verdict"]
            c[1] += 1
        for (rung, fr), (k, n) in sorted(cells.items()):
            print(f"  accuracy vs gold {rung} {fr}: {k}/{n}")
        bands = json.loads(Path(a.bands).read_text()) if Path(a.bands).exists() else {}
        band = bands.get(key)
        if band and not (ds / "responses" / f"{band['run']}.jsonl").exists():
            print(f"  reference band points to a run that is not released ({band['run']}): FAIL")
            ok = False
            band = None
        if band:
            ref = {r["prompt_id"]: r for r in read_jsonl(ds / "responses" / f"{band['run']}.jsonl")}
            pairs = [(got[p], ref[p]) for p in got if p in ref and "error" not in got[p]]
            agree = sum(a_.get("decision") == b_.get("decision") for a_, b_ in pairs) / max(1, len(pairs))
            diffs = [abs(a_["lo_conv"] - b_["lo_conv"]) for a_, b_ in pairs if a_.get("lo_conv") is not None and b_.get("lo_conv") is not None]
            mad = sum(diffs) / len(diffs) if diffs else 0.0
            okb = len(pairs) >= band.get("min_pairs", 1) and agree >= band["min_agreement"] and mad <= band["max_mean_abs_diff"]
            print(f"  reference band ({band['run']}): agreement {agree:.3f} (>= {band['min_agreement']}), "
                  f"mean |Δ lo| {mad:.2f} (<= {band['max_mean_abs_diff']}) on {len(pairs)} prompts: {'PASS' if okb else 'FAIL'}")
            ok &= okb
        else:
            print("  no reference band for this model: new model accepted; slice results above are its first numbers")
    print("  step 3", "PASS" if ok else "FAIL")
    return ok
