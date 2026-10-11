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
    if not anchored:
        state = "unreadable"
    elif bad:
        state = "red" if len(bad) == len(anchored) else "amber"
    else:
        # A24: open square only where every readable framing applies the law in force; an interval spanning zero is
        # shown as undetermined, not as the law in force
        state = "ok" if all(e["status"] in ("a", "held") for e in anchored) else "undetermined"
    # post hoc (A12): the paired score difference variant - reference lies below zero in the Ja/Nein framing, i.e. the
    # model registers the fact although its decision stays on the convicting side
    drop = state in ("red", "amber") and conv.get("ci_diff") is not None and conv["ci_diff"][1] < 0
    return dict(state=state, k=conv["v_convicted"], n=conv["n"], drop=drop)


def _mark(ax, x, y, state, size=6.4):
    """One cell of the synopsis, readable in greyscale: filled square = a law not in force is applied in every readable
    framing; half-filled = in one framing; open square = the law in force is applied; dash = the base itself is not
    convicted, so the element cannot be read."""
    if state == "unreadable":
        ax.plot([x - 0.09, x + 0.09], [y, y], color=GREY, lw=0.9, solid_capstyle="butt")
        return
    if state == "undetermined":                      # A24: the interval spans zero
        ax.plot([x], [y], marker="s", ms=size, mew=0.8, linestyle="none", mfc=PAPER, mec=GREY)
        ax.plot([x], [y], marker="o", ms=size * 0.3, linestyle="none", mfc=GREY, mec=GREY)
        return
    kw = dict(marker="s", ms=size, mew=0.8, linestyle="none")
    if state == "red":
        ax.plot([x], [y], color=RED, mfc=RED, mec=RED, **kw)
    elif state == "amber":
        ax.plot([x], [y], color=RED, mfc=RED, mec=RED, fillstyle="left", markerfacecoloralt=PAPER, **kw)
    else:
        ax.plot([x], [y], mfc=PAPER, mec=INK, **kw)


def fig_synopse(R, out, blocks=SYN_BLOCKS):
    """The law in force next to the law the model applies: one row per legal fact changed, one column per rung and
    model block; marks instead of numbers so the pattern reads at print size and in greyscale."""
    blocks = [b for b in blocks if b[0] in R["runs"]]
    rows = [r for r in SYN_ROWS if any(e["edit"] == r[0] and e.get("subset") == "core"
                                       for b in blocks for e in R["runs"][b[0]]["edits"])]

    def rungs_of(b):
        have = {e["rung"] for e in R["runs"][b[0]]["edits"] if e.get("subset") == "core" and e["lang"] == b[1]}
        return [r for r in RUNGS_ALL if r in have]
    fig, ax = plt.subplots(figsize=(7.3, 0.205 * len(rows) + 0.95))
    ax.set_axis_off()
    x0, cw, gap = 3.25, 0.30, 0.22
    cols, x = [], x0
    for b in blocks:
        rs = rungs_of(b)
        ax.text(x - 0.12, -1.55, b[2], fontsize=7.0, fontweight="semibold", color=INK)
        ax.plot([x - 0.12, x + (len(rs) - 1) * cw + 0.12], [-1.2, -1.2], color=INK, lw=0.5)
        for rung in rs:
            ax.text(x, -0.75, rung, ha="center", fontfamily=MONO, fontsize=6.2, color=INK2)
            cols.append((b, rung, x))
            x += cw
        x += gap
    right = x - gap + 0.15
    ax.text(0, -1.55, "One fact changed", fontsize=7.2, fontweight="semibold")
    ax.text(2.55, -1.55, "Law", fontsize=7.2, fontweight="semibold")
    for i, (edit, label, law, src) in enumerate(rows):
        if i and rows[i - 1][2] != law:
            ax.plot([0, right], [i - 0.5, i - 0.5], color=INK, lw=0.5)
        ax.text(0, i, label, va="center", fontsize=7.0)
        ax.text(2.55, i, law, va="center", fontsize=6.5, fontfamily=MONO)
        for b, rung, xx in cols:
            c = _syn_cell(R["runs"][b[0]]["edits"], b[1], edit, rung)
            if c is not None:
                _mark(ax, xx, i, c["state"])
    # legend, in the figure itself so the encoding is never separated from it
    ly = len(rows) + 0.35
    items = [("red", "a law not in force is applied (both framings)"), ("amber", "in one framing"),
             ("ok", "the law in force is applied"), ("undetermined", "undetermined (interval spans 0)"),
             ("unreadable", "base not convicted: cannot be read")]
    lx = 0.0
    for state, text in items:
        _mark(ax, lx + 0.08, ly, state, size=5.6)
        ax.text(lx + 0.22, ly, text, va="center", fontsize=6.6, color=INK2)
        lx += 0.42 + 0.047 * len(text)
    ax.set_xlim(-0.05, right + 0.05)
    ax.set_ylim(len(rows) + 0.85, -1.95)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    save(fig, out, "fig1_synopse")


# ------------------------------------------------------------------------------------------- method (diagram)
def fig_method(out):
    """From pinned law to the per-element read-back (one row of boxes), and below it the checks on the gold. Sized to
    be read at A4 text width: box titles about 8.5 pt, sub-lines about 7.5 pt."""
    steps = [("Pinned law", "Fedlex texts,\nBGE 130 IV 111"), ("Gold by code", "element model\n\u2192 verdict"),
             ("Minimal twins", "one legal fact\nchanged"), ("Prompts", "rungs R0\u2013R6,\ntwo framings"),
             ("Apertus", "forced choice,\nfree text"), ("Read-back", "the law it applies,\nper element")]
    fig, ax = plt.subplots(figsize=(7.0, 1.42))
    ax.set_axis_off()
    n, g = len(steps), 0.028
    w = (1 - g * (n - 1)) / n
    y0, h = 0.42, 0.53
    for k, (head, sub) in enumerate(steps):
        x = k * (w + g)
        ax.add_patch(plt.Rectangle((x, y0), w, h, facecolor=PAPER, edgecolor=INK, lw=0.7))
        ax.text(x + 0.012, y0 + h - 0.07, head, fontsize=9.0, fontweight="semibold", va="top", color=INK)
        ax.text(x + 0.012, y0 + 0.06, sub, fontsize=7.9, va="bottom", color=INK2, linespacing=1.15)
        if k:
            ax.annotate("", xy=(x - 0.003, y0 + h / 2), xytext=(x - g + 0.003, y0 + h / 2),
                        arrowprops=dict(arrowstyle="-|>", lw=0.7, color=INK, mutation_scale=8))
    # the checks hang off the gold box
    gx = 1 * (w + g) + w / 2
    ax.plot([gx, gx], [y0, 0.22], color=RED, lw=0.7)
    ax.plot([gx, gx + 0.012], [0.22, 0.22], color=RED, lw=0.7)
    ax.text(gx + 0.018, 0.22, "Gold checked against: blind annotation by Claude agents and by Qwen (another model family),\n"
            "Swiss court rulings, mutation tests, and the official text in German, French and Italian",
            fontsize=7.9, color=RED, va="center", ha="left", linespacing=1.2)
    ax.set_xlim(-0.004, 1.004)
    ax.set_ylim(0.04, 0.99)
    fig.subplots_adjust(left=0.004, right=0.996, top=0.995, bottom=0.005)
    save(fig, out, "fig0_method")


# ------------------------------------------------------------------------------------------- rungs (chart)
RUNG_SERIES = [("publicai-70b-fc-core", "de", "70B DE", INK, "s", "-", True),
               ("publicai-70b-fc-core-fr", "fr", "70B FR", INK, "^", "-", True),
               ("publicai-70b-fc-core-it", "it", "70B IT", INK, "o", "-", True),
               ("8b-gguf-q4_k_m-cpu-core", "de", "8B DE", INK2, "D", "--", False),
               ("publicai-70b-fc-lay", "de_lay", "70B DE, first person", INK2, "s", ":", False)]
RUNG_X = ("R0", "R3", "R4", "R5")


def fig_rungs(R, out, framing="conv"):
    """Small multiples, one panel per model and language: share of acquittals recognised (solid) and of convictions
    kept (dashed) by rung, Ja/Nein."""
    series = [s for s in RUNG_SERIES if s[0] in R["runs"]]
    fig, axes = plt.subplots(1, len(series), figsize=(7.3, 1.9), sharey=True)
    for ax, (run, lang, label, *_rest) in zip(axes, series):
        acc = {a["rung"]: a for a in R["runs"][run]["accuracy"]
               if a.get("subset") == "core" and a["lang"] == lang and a["framing"] == framing}
        xs = [k for k, r in enumerate(RUNG_X) if r in acc]
        for side, ls, mfc, col in (("acquit", "-", INK, INK), ("convict", "--", PAPER, INK2)):
            ys = [acc[RUNG_X[k]][f"{side}_correct"] / acc[RUNG_X[k]][f"{side}_n"] for k in xs]
            # R5 replaces the rules with the verbatim law: drawn as its own point, not joined to R4 (A24)
            cut = [i for i, k in enumerate(xs) if RUNG_X[k] in ("R5", "R6")]
            seg = len(xs) if not cut else cut[0]
            ax.plot(xs[:seg], ys[:seg], color=col, lw=1.0, ls=ls, marker="o", ms=3.6, mfc=mfc, mec=col, mew=0.8, zorder=3)
            if cut:
                ax.plot(xs[seg:], ys[seg:], color=col, lw=1.0, ls=ls, marker="o", ms=3.6, mfc=mfc, mec=col, mew=0.8,
                        zorder=3)
        ax.set_xticks(range(len(RUNG_X)), RUNG_X)
        ax.set_xlim(-0.35, len(RUNG_X) - 0.65)
        ax.set_ylim(-0.04, 1.06)
        ax.set_yticks([0, 0.5, 1], ["0", "0.5", "1"])
        for t in ax.get_xticklabels() + ax.get_yticklabels():
            t.set_fontfamily(MONO)
            t.set_fontsize(8)
        ax.axhline(1.0, color=LINE, lw=0.5, zorder=1)
        ax.set_title(label.replace("70B DE, user voice", "70B DE, first person"), fontsize=8.6, pad=3)
    axes[0].set_ylabel("share", fontsize=8.4, labelpad=2)
    h = [plt.Line2D([], [], color=INK, lw=1.0, marker="o", ms=3.6, mfc=INK),
         plt.Line2D([], [], color=INK2, lw=1.0, ls="--", marker="o", ms=3.6, mfc=PAPER, mec=INK2)]
    fig.legend(h, ["acquittals recognised (of 215)", "convictions kept (of 430)"], loc="upper left", ncol=2,
               bbox_to_anchor=(0.045, 1.04), fontsize=8.4, handlelength=2.6, columnspacing=1.8)
    fig.subplots_adjust(left=0.05, right=0.995, wspace=0.12, top=0.74, bottom=0.14)
    save(fig, out, "fig2_rungs")


def main(results: str, out: str):
    R = json.loads(Path(results).read_text())
    out = Path(out)
    fig_method(out)
    fig_synopse(R, out)
    fig_rungs(R, out)
    fig_stage(R, out)
    fig_builds(R, out)
    print("figures written to", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
