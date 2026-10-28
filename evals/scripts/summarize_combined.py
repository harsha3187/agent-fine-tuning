"""Summarize combined (original + synthetic) results per model on the pooled set."""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

PRICES = {  # USD per 1M tokens (input, output)
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.6-terra": (2.00, 12.00),
    "gpt-5.6-sol": (4.00, 20.00),
    "mai-code-1-1-flash": (0.20, 1.20),
}
TASKS = ("product", "shop", "voucher", "compound")
ROOT = Path(__file__).resolve().parents[2]


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x.strip()]


def mean_ci(values: list[float], seed: int = 7) -> tuple[float, float, float]:
    if not values:
        return math.nan, math.nan, math.nan
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(values, k=len(values))) / len(values) for _ in range(1000))
    return sum(values) / len(values), means[25], means[974]


def price_of(model: str) -> tuple[float, float]:
    key = next((k for k in PRICES if model.startswith(k)), None)
    return PRICES[key] if key else (math.nan, math.nan)


def summarize(root: Path, stage: str, split: str) -> None:
    models = sorted(p.name for p in (root / stage).iterdir() if p.is_dir())
    header = f"{'model':16s} {'task':9s} {'n':>4s} {'score [95% CI]':>22s} {'success':>8s} {'lat(s)':>7s} {'tok/ep':>8s} {'$/1k ep':>8s}"
    print(header)
    for model in models:
        pin, pout = price_of(model)
        pooled: list[dict] = []
        for task in (*TASKS, "ALL"):
            data = pooled if task == "ALL" else rows(root / stage / model / split / f"{task}.jsonl")
            if task != "ALL":
                pooled += data
            if not data:
                continue
            scores = [float(r["grade"]["score"]) for r in data]
            m, lo, hi = mean_ci(scores)
            succ = sum(bool(r["grade"].get("success")) for r in data) / len(data)
            lat = sum(r["latency_seconds"] for r in data) / len(data)
            tin = sum(r["usage"]["input_tokens"] for r in data) / len(data)
            tout = sum(r["usage"]["output_tokens"] for r in data) / len(data)
            cost = (tin * pin + tout * pout) / 1e6 * 1000
            label = "ALL (pooled)" if task == "ALL" else task
            print(f"{model:16s} {label:9s} {len(data):4d} {m:6.3f} [{lo:.3f},{hi:.3f}] {succ:8.1%} {lat:7.1f} {tin + tout:8.0f} {cost:8.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="baseline")
    ap.add_argument("--split", default="development")
    a = ap.parse_args()
    summarize(ROOT / "evals" / "results" / "combined", a.stage, a.split)
