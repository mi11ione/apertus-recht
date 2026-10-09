"""Second-annotator agreement with the code gold, and the human adjudication queue.

    python scripts/annotation_agreement.py <labels_dir>

Reads the blind annotator files (labels_<k>.json, opaque ids), maps them back with review/annotation/blind_ids.json and
writes, under statutes/stgb_261bis/review/annotation/:
  labels.jsonl              one row per annotated item: item id, annotator label/element/confidence/reason
  agreement.json            agreement and Cohen's kappa with the gold (overall, per language, per family, per variant)
  adjudication_queue.jsonl  every disagreement, every contested item, and a seeded 10% sample of agreeing settled items,
                            shuffled, with the group hidden (the adjudicator sees text, gold and annotator label)
"""
import collections
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from statute_twins.analysis.stats import cohen_kappa, wilson  # noqa: E402
from statute_twins.qc.checks import load_items  # noqa: E402

OUT = ROOT / "statutes/stgb_261bis/review/annotation"
ELEM = {"none": "all_met", "setting": "setting", "characteristic": "characteristic", "act_date": "act_date"}


def main(labels_dir: str) -> None:
    blind = json.loads((OUT / "blind_ids.json").read_text())
    items = {i["id"]: i for i in load_items(ROOT / "dataset")}
    rows = []
    for p in sorted(Path(labels_dir).glob("labels_*.json")):
        for r in json.loads(p.read_text()):
            iid = blind[r["id"]]
            rows.append(dict(item_id=iid, blind_id=r["id"], annotator=f"claude-agent-{p.stem.split('_')[1]}",
                             label=r["label"], deciding_element=r["deciding_element"], confidence=r["confidence"],
                             reason=r["reason"], note=r.get("note", "")))
    assert len({r["item_id"] for r in rows}) == len(rows) == len(blind), "missing or duplicate labels"
    (OUT / "labels.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in sorted(rows, key=lambda r: r["item_id"])))

    def summarise(sel):
        g = [items[r["item_id"]]["gold_verdict"] for r in sel]
        a = [r["label"] for r in sel]
        k = sum(x == y for x, y in zip(g, a))
        el = [r for r, gg, aa in zip(sel, g, a) if gg == aa == "acquit"]
        el_ok = sum(ELEM.get(r["deciding_element"]) == items[r["item_id"]]["deciding_element"] for r in el)
        return dict(n=len(sel), agree=k, agreement=k / len(sel), agreement_ci=wilson(k, len(sel)),
                    kappa=cohen_kappa(g, a), deciding_element_agree=el_ok, deciding_element_n=len(el),
                    confusion={f"{x}->{y}": n for (x, y), n in sorted(collections.Counter(zip(g, a)).items())})

    by = collections.defaultdict(list)
    for r in rows:
        i = items[r["item_id"]]
        by[("all",)].append(r)
        by[("lang", i["lang"])].append(r)
        by[("family", i["family"])].append(r)
        by[("variant", i["variant"])].append(r)
    agreement = {":".join(k): summarise(v) for k, v in sorted(by.items())}
    (OUT / "agreement.json").write_text(json.dumps(agreement, indent=1) + "\n")

    rng = random.Random(1010)
    dis = [r for r in rows if r["label"] != items[r["item_id"]]["gold_verdict"]]
    cont = [r for r in rows if items[r["item_id"]]["label"] == "contested" and r not in dis]
    agree_settled = sorted((r for r in rows if r not in dis and r not in cont), key=lambda r: r["item_id"])
    sample = rng.sample(agree_settled, round(0.10 * len(agree_settled)))
    queue = [dict(r, queue_reason="disagreement") for r in dis] + [dict(r, queue_reason="contested") for r in cont] + \
            [dict(r, queue_reason="blind_sample") for r in sample]
    rng.shuffle(queue)
    q = []
    for n, r in enumerate(queue, 1):
        i = items[r["item_id"]]
        q.append(dict(n=n, item_id=r["item_id"], lang=i["lang"], text=i["text"], gold_verdict=i["gold_verdict"],
                      gold_reason=i["gold_reason"], rationale=i["rationale"], annotator_label=r["label"],
                      annotator_element=r["deciding_element"], annotator_reason=r["reason"], annotator_note=r["note"],
                      queue_reason=r["queue_reason"]))
    (OUT / "adjudication_queue.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in q))
    a = agreement["all"]
    print(json.dumps(dict(n=a["n"], agreement=round(a["agreement"], 4), kappa=round(a["kappa"], 4), confusion=a["confusion"],
                          queue=dict(collections.Counter(x["queue_reason"] for x in q))), indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
