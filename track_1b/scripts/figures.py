"""Report figures, generated from results/results.json only (no model, no network).

    python scripts/figures.py results/results.json docs/figures

Visual language: Swiss administrative sobriety (humanist sans, strict left grid, one red) with technical-manual
detailing (monospace codes, hairlines, square marks). Red is reserved for "the model applies a law that is not the
law in force"; everything else is ink and greys. Fonts are vendored in docs/fonts (SIL OFL).
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INK, INK2, LINE, PAPER, RED, GREY = "#111111", "#5f5f5f", "#cfcfcb", "#ffffff", "#dc0018", "#9a9a96"
for f in (ROOT / "docs/fonts").glob("*.ttf"):
    font_manager.fontManager.addfont(str(f))
SANS, MONO = "Source Sans 3", "IBM Plex Mono"
plt.rcParams.update({
    "font.family": SANS, "font.size": 8.5, "axes.edgecolor": INK, "axes.linewidth": 0.6, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "axes.titlesize": 9.5,
    "axes.titleweight": "semibold", "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER, "pdf.fonttype": 42,
    "axes.grid": False, "legend.frameon": False, "legend.fontsize": 7.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.major.size": 3, "ytick.major.size": 3,
})


def caption(fig, ax, number: int, text: str):
    """Numbered caption below the plot, aligned with the axes' left edge (document convention, not a chart title)."""
    x0 = ax.get_position().x0
    fig.text(x0, -0.07, f"Fig. {number}", fontsize=8, fontweight="semibold", color=INK, va="top")
    fig.text(x0 + 0.06, -0.07, text, fontsize=8, color=INK, va="top", wrap=True)


def save(fig, out: Path, name: str):
    out.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"{name}.{ext}", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------------------------------- stage trajectory
STAGE_X = [("8b-bf16-RLVR", "RLVR"), ("8b-bf16-blend-RLVR-DPO-a0.25", "0.25"), ("8b-bf16-blend-RLVR-DPO-a0.5", "0.50"),
           ("8b-bf16-blend-RLVR-DPO-a0.75", "0.75"), ("8b-bf16-DPO", "DPO")]
STAGE_EDITS = [("characteristic:not_yet_covered", "R3", "conv", "sexual orientation, act in 2019, law stated", INK),
               ("setting:failed", "R0", "conv", "family dinner, no law in the prompt", INK),
               ("characteristic:not_listed|canton", "R3", "conv", "canton, closed list stated", RED),
               ("characteristic:not_listed|occupation", "R3", "conv", "occupation, closed list stated", GREY),
               ("setting:failed", "R3", "conv", "family dinner, BGE rule stated", GREY)]


def fig_stage(R, out):
    traj = R["comparisons"]["stage_trajectory"]
    idx = {(t["run"], t["edit"], t["rung"], t["framing"]): t for t in traj}
    fig, ax = plt.subplots(figsize=(6.6, 2.8))
    xs = list(range(len(STAGE_X)))
    ends = []
    for edit, rung, fr, label, col in STAGE_EDITS:
        pts = [(x, idx.get((run, edit, rung, fr))) for x, (run, _) in zip(xs, STAGE_X)]
        pts = [(x, t) for x, t in pts if t and t["mean_v"] is not None]
        ax.plot([x for x, _ in pts], [t["mean_v"] for _, t in pts], color=col, lw=1.4 if col == RED else 1.0, zorder=3)
        ax.scatter([x for x, _ in pts], [t["mean_v"] for _, t in pts], s=14, marker="s", color=col, zorder=4, linewidths=0)
        last = pts[-1][1]
        ends.append([last["mean_v"], f"{label}   {last['v_convicted']}/{last['n']}", col])
    ends.sort(key=lambda e: e[0])
    for k in range(1, len(ends)):                       # keep end labels at least 2.6 nats apart
        ends[k][0] = max(ends[k][0], ends[k - 1][0] + 2.6)
    for y, text, col in ends:
        ax.text(len(xs) - 1 + 0.15, y, text, va="center", fontsize=7.2, color=col)
    ax.axhline(0, color=INK, lw=0.5)
    ax.set_xticks(xs, [l for _, l in STAGE_X], fontfamily=MONO)
    ax.set_xlim(-0.2, len(xs) + 1.9)
    ax.spines["bottom"].set_bounds(0, len(xs) - 1)
    ax.set_xlabel("RLVR → DPO, exact bf16 weight blends (share of DPO)", fontsize=7.5, color=INK2, loc="left")
    ax.set_ylabel("log-odds of conviction, mean (nats)")
    for t in ax.get_yticklabels():
        t.set_fontfamily(MONO)
    caption(fig, ax, 3, "Five scenarios the statute acquits, along the post-training step from RLVR to DPO of Apertus "
            "v1.5 8B (Ja/Nein framing; frames L15–L20, the same items at every point). Above zero the model convicts. "
            "End labels: convictions k/n under DPO.")
    save(fig, out, "fig3_stage")


# ------------------------------------------------------------------------------------------- build parity
BUILDS = [("8b-gguf-q8_0", "GGUF Q8_0 (public)"), ("8b-gguf-q4_k_m", "GGUF Q4_K_M (public)"),
          ("8b-mlx4-DPO", "MLX 4-bit g64, DPO"), ("8b-mlx4-final", "MLX 4-bit g64, final"),
          ("8b-bf16-RLVR", "bf16 RLVR (previous stage)"), ("publicai-70b-fc", "70B, Public AI")]
CELLS = [("conv_R0", "Ja/Nein R0"), ("conv_R3", "Ja/Nein R3"), ("ver_R0", "Urteil R0"), ("ver_R3", "Urteil R3")]


def fig_builds(R, out):
    bp = R["comparisons"]["build_parity"]
    rows = [(k, l) for k, l in BUILDS if k in bp]
    fig, ax = plt.subplots(figsize=(6.6, 2.3))
    ax.grid(False)
    for i, (k, label) in enumerate(rows):
        for j, (c, _) in enumerate(CELLS):
            v = bp[k]["cells"].get(c)
            frac = v["agree"] / v["n"]
            shade = 1 - (1 - frac) * 4          # 100% -> white, 75% -> black
            col = str(max(0.0, min(1.0, 0.72 + 0.28 * shade)))
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=col, edgecolor=LINE, lw=0.5))
            low = frac < 0.9
            ax.text(j + 0.5, i + 0.5, f"{v['agree']}/{v['n']}", ha="center", va="center", fontfamily=MONO, fontsize=7,
                    color=RED if low else INK)
        tot = bp[k]
        ax.text(len(CELLS) + 0.15, i + 0.5, f"{tot['agree']}/{tot['n']}  {tot['mean_abs_diff']:5.2f}",
                va="center", fontfamily=MONO, fontsize=7, color=RED if tot["agree"] / tot["n"] < 0.9 else INK)
    ax.set_xlim(0, len(CELLS) + 1.9)
    ax.set_ylim(len(rows), 0)
    ax.set_xticks([j + 0.5 for j in range(len(CELLS))], [l for _, l in CELLS], fontfamily=MONO)
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(len(rows))], [l for _, l in rows], color=INK)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.text(len(CELLS) + 0.15, -0.12, "all 648    mean |Δ|", fontsize=7.5, color=INK2)
    caption(fig, ax, 4, "Decisions that agree with Apertus v1.5 8B DPO in bf16, per framing and rung (162 prompts per "
            "cell, 648 in all), and mean absolute difference in log-odds. Red: below 90% agreement.")
    save(fig, out, "fig4_builds")


def main(results: str, out: str):
    R = json.loads(Path(results).read_text())
    out = Path(out)
    fig_stage(R, out)
    fig_builds(R, out)
    print("figures written to", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
