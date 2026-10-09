"""Small, dependency-free statistics: seeded percentile bootstrap, Wilson interval, Cohen's kappa."""
from __future__ import annotations

import math
import random

B_DEFAULT = 2000


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def bootstrap_ci(xs, b: int = B_DEFAULT, seed: int = 0, alpha: float = 0.05, stat=mean) -> tuple[float, float]:
    """Percentile bootstrap CI of ``stat`` over items (resampling items with replacement)."""
    xs = list(xs)
    if not xs:
        return (float("nan"), float("nan"))
    if len(xs) == 1:
        return (xs[0], xs[0])
    rng = random.Random(seed)
    n = len(xs)
    reps = sorted(stat([xs[rng.randrange(n)] for _ in range(n)]) for _ in range(b))
    lo = reps[int(math.floor(alpha / 2 * b))]
    hi = reps[min(b - 1, int(math.ceil((1 - alpha / 2) * b)) - 1)]
    return (lo, hi)


def paired_bootstrap_ci(pairs, b: int = B_DEFAULT, seed: int = 0, alpha: float = 0.05):
    """CI of mean(v) , mean(ref) and mean(v - ref), resampling pairs jointly."""
    pairs = list(pairs)
    if not pairs:
        nan = (float("nan"), float("nan"))
        return nan, nan, nan
    rng = random.Random(seed)
    n = len(pairs)
    a, r, dd = [], [], []
    for _ in range(b):
        s = [pairs[rng.randrange(n)] for _ in range(n)]
        mv, mr = mean(p[0] for p in s), mean(p[1] for p in s)
        a.append(mv), r.append(mr), dd.append(mv - mr)
    out = []
    for reps in (a, r, dd):
        reps.sort()
        out.append((reps[int(math.floor(alpha / 2 * b))], reps[min(b - 1, int(math.ceil((1 - alpha / 2) * b)) - 1)]))
    return tuple(out)


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def cohen_kappa(a: list, b: list) -> float:
    assert len(a) == len(b) and a
    labels = sorted(set(a) | set(b))
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labels)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)
