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
    return None   # captions are set in the report text (document convention), not baked into the images


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


# ------------------------------------------------------------------------------------------- Synopse
SYN_ROWS = [
    ("setting:failed", "Statement only among family or friends", "acquit", "BGE 130 IV 111 E. 5.2"),
    ("characteristic:not_listed|canton", "Group defined by canton", "acquit", "closed list"),
    ("characteristic:not_listed|occupation", "Group defined by occupation", "acquit", "closed list"),
    ("characteristic:not_listed|age", "Group defined by age", "acquit", "closed list"),
    ("characteristic:not_listed|gender_identity", "Group defined by gender identity", "acquit", "closed list; Pa.Iv. 13.407"),
    ("characteristic:not_listed|sex", "Group defined by sex", "acquit", "closed list"),
    ("characteristic:not_listed|disability", "Group defined by disability", "acquit", "closed list"),
    ("characteristic:not_listed|political_opinion", "Group defined by political opinion", "acquit", "closed list"),
    ("characteristic:not_yet_covered", "Sexual orientation, act before 1 Jul 2020", "acquit", "AS 2020 1609; Art. 2"),
    ("act_date:not_in_force", "Any group, act before 1995", "acquit", "AS 1994 2887; Art. 2"),
    ("placebo|family_wording", "Public statement in family wording", "convict", "BGE 130 IV 111"),
    ("placebo|synonym", "Listed characteristic, other word", "convict", "Art. 261bis"),
    ("placebo|date_overapplied", "Race, ethnicity, religion, act 2018–20", "convict", "AS 1994 2887"),
    ("placebo|date", "Sexual orientation, 1 Jul or Aug 2020", "convict", "AS 2020 1609"),
]
SYN_BLOCKS = [("publicai-70b-fc-core", "de", "70B · Deutsch"), ("publicai-70b-fc-core-fr", "fr", "70B · Français"),
              ("publicai-70b-fc-core-it", "it", "70B · Italiano"), ("8b-gguf-q4_k_m-cpu-core", "de", "8B Q4_K_M · Deutsch")]
RUNGS_ALL = ("R0", "R3", "R4", "R5")
RUNGS3 = ("R0", "R3", "R4")


def _syn_cell(edits_run, lang, edit, rung):
    es = [e for e in edits_run if e.get("subset") == "core" and e["lang"] == lang and e["edit"] == edit and e["rung"] == rung]
    if not es:
        return None
    anchored = [e for e in es if e["status"] != "u"]
    bad = [e for e in anchored if e["status"] in ("F", "broken")]
    conv = next((e for e in es if e["framing"] == "conv"), es[0])
    state = "unreadable" if not anchored else ("red" if len(bad) == len(anchored) else ("amber" if bad else "ok"))
    return dict(state=state, k=conv["v_convicted"], n=conv["n"])


def fig_synopse(R, out, blocks=SYN_BLOCKS):
    blocks = [b for b in blocks if b[0] in R["runs"]]
    rows = [r for r in SYN_ROWS if any(e["edit"] == r[0] and e.get("subset") == "core"
                                       for b in blocks for e in R["runs"][b[0]]["edits"])]
    # each block shows the rungs its run has (R5, the verbatim law, was run in German only)
    def rungs_of(b):
        have = {e["rung"] for e in R["runs"][b[0]]["edits"] if e.get("subset") == "core" and e["lang"] == b[1]}
        return [r for r in RUNGS_ALL if r in have]
    cols = [(b, rung) for b in blocks for rung in rungs_of(b)]
    fig, ax = plt.subplots(figsize=(7.3, 0.22 * len(rows) + 0.6))
    ax.set_axis_off()
    x0, cw, gap = 3.55, 0.47, 0.12
    tint = {"red": "#f6c5cb", "amber": "#fbe3e6", "ok": PAPER, "unreadable": "#e6e6e3"}
    xs = []
    block_index = {b: k for k, b in enumerate(dict.fromkeys(b for b, _ in cols))}
    for j, (b, rung) in enumerate(cols):
        xx = x0 + j * cw + block_index[b] * gap
        xs.append(xx)
        ax.text(xx + cw / 2, -0.55, rung, ha="center", fontfamily=MONO, fontsize=6.2, color=INK2)
        if rung == "R0":
            ax.text(xx, -1.35, b[2], fontsize=6.9, color=INK, fontweight="semibold")
            nb = sum(1 for bb, _ in cols if bb == b)
            ax.plot([xx, xx + nb * cw - 0.04], [-1.05, -1.05], color=INK, lw=0.5)
    ax.text(0, -1.35, "One fact changed", fontsize=7.2, fontweight="semibold")
    ax.text(2.85, -1.35, "Law", fontsize=7.2, fontweight="semibold")
    right = xs[-1] + cw
    for i, (edit, label, law, src) in enumerate(rows):
        y = i
        if i and rows[i - 1][2] != law:
            ax.plot([0, right], [y - 0.5, y - 0.5], color=INK, lw=0.5)
        ax.text(0, y, label, va="center", fontsize=7.0)
        ax.text(2.85, y, law, va="center", fontsize=6.6, fontfamily=MONO)
        for xx, (b, rung) in zip(xs, cols):
            c = _syn_cell(R["runs"][b[0]]["edits"], b[1], edit, rung)
            if c is None:
                ax.text(xx + cw / 2, y, "·", ha="center", va="center", color=GREY)
                continue
            ax.add_patch(plt.Rectangle((xx + 0.015, y - 0.42), cw - 0.03, 0.84, facecolor=tint[c["state"]], edgecolor="none"))
            ax.text(xx + cw / 2, y, f"{c['k']}/{c['n']}", ha="center", va="center", fontfamily=MONO, fontsize=5.6,
                    color=RED if c["state"] == "red" else INK)
    ax.set_xlim(-0.05, right + 0.05)
    ax.set_ylim(len(rows) - 0.45, -1.75)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    save(fig, out, "fig1_synopse")


def main(results: str, out: str):
    R = json.loads(Path(results).read_text())
    out = Path(out)
    fig_synopse(R, out)
    fig_stage(R, out)
    fig_builds(R, out)
    print("figures written to", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
