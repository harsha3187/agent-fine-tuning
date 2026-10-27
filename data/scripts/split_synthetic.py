"""Group-disjoint split of synthetic cases and search-document build (targets + distractors)."""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from synthesize import CATALOG, ROOT, build_index

from shoppingbench_foundry.grading import _normalize

SYN = ROOT / "data" / "synthetic"
TASKS = ("product", "shop", "voucher", "compound")
FRACTIONS = {"train": 0.80, "val": 0.10, "heldout": 0.10}
SHOP_DISTRACTORS = 4
RANDOM_DISTRACTORS = 3


def pids(case: dict) -> list[str]:
    return [str(r["product_id"]) for r in case["reward"]] if isinstance(case["reward"], list) \
        else [str(case["reward"]["product_id"])]


def rewards(case: dict) -> list[dict]:
    return case["reward"] if isinstance(case["reward"], list) else [case["reward"]]


def load_prepared() -> tuple[set[str], dict[str, set[str]]]:
    ids: set[str] = set()
    titles: dict[str, set[str]] = defaultdict(set)
    path = ROOT / "data" / "prepared" / "search-documents.jsonl"
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.strip():
            product = json.loads(line)["product"]
            ids.add(str(product["product_id"]))
            titles[_normalize(product.get("title", ""))].add(str(product["product_id"]))
    return ids, titles


def original_gold_titles() -> set[str]:
    found: set[str] = set()
    for task in ("product", "shop", "voucher"):
        for line in (ROOT / "data" / "source" / f"{task}.jsonl").read_text(encoding="utf-8").split("\n"):
            if line.strip():
                for reward in rewards(json.loads(line)):
                    found.update(_normalize(t) for t in reward["title"])
    return found


def components(cases: list[dict]) -> list[list[int]]:
    parent = list(range(len(cases)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner: dict[str, int] = {}
    for i, case in enumerate(cases):
        keys = [f"p{p}" for p in pids(case)] + [f"s{s}" for s in case["meta"]["shop_ids"]]
        for key in keys:
            if key in owner:
                parent[find(i)] = find(owner[key])
            else:
                owner[key] = i
    groups = defaultdict(list)
    for i in range(len(cases)):
        groups[find(i)].append(i)
    return list(groups.values())


def main() -> None:
    cases = []
    for task in TASKS:
        for line in (SYN / "validated" / f"{task}.jsonl").read_text(encoding="utf-8").split("\n"):
            if line.strip():
                cases.append(json.loads(line))
    rng = random.Random(11)
    groups = components(cases)
    rng.shuffle(groups)
    # Fill splits group by group so that no product or shop crosses a split.
    split_of: dict[int, str] = {}
    totals = {name: 0 for name in FRACTIONS}
    for group in groups:
        name = min(FRACTIONS, key=lambda n: totals[n] / FRACTIONS[n])
        totals[name] += len(group)
        for i in group:
            split_of[i] = name
    rows, shops = build_index()
    by_pid = {pid: (shop, off) for pid, shop, off in rows}
    chosen: dict[str, int] = {}
    for case in cases:
        for pid in pids(case):
            shop, off = by_pid[pid]
            chosen[pid] = off
            peers = [r for r in shops[shop] if rows[r][0] != pid]
            for r in rng.sample(peers, min(SHOP_DISTRACTORS, len(peers))):
                chosen.setdefault(rows[r][0], rows[r][2])
    for _ in range(len(cases) * RANDOM_DISTRACTORS):
        pid, _, off = rows[rng.randrange(len(rows))]
        chosen.setdefault(pid, off)
    lines: dict[str, tuple[str, str]] = {}
    with CATALOG.open("rb") as src:
        for pid, off in chosen.items():
            src.seek(off)
            line = src.readline().decode("utf-8").rstrip("\n")
            lines[pid] = (_normalize(json.loads(line)["product"].get("title", "")), line)

    # The served index is the original controlled catalog plus these documents, so the
    # ambiguity gate must run against the combined set, not the synthetic set alone.
    prepared_ids, prepared_titles = load_prepared()
    orig_gold_titles = original_gold_titles()
    eligible = [
        i for i, case in enumerate(cases)
        if not any(p in prepared_ids for p in pids(case))
        and not any(_normalize(t) in orig_gold_titles for r in rewards(case) for t in r["title"])
    ]
    gold_ids = {p for i in eligible for p in pids(cases[i])}
    syn_gold_titles = {_normalize(t) for i in eligible for r in rewards(cases[i]) for t in r["title"]}
    blocked = orig_gold_titles | syn_gold_titles
    for pid in [p for p in lines if p not in gold_ids and (p in prepared_ids or lines[p][0] in blocked)]:
        del lines[pid]
    served: dict[str, set[str]] = defaultdict(set)
    for pid, (title, _) in lines.items():
        served[title].add(pid)
    for title, ids in prepared_titles.items():
        served[title] |= ids

    kept_idx = {
        i for i in eligible
        if not any(served[_normalize(t)] - {str(r["product_id"])} for r in rewards(cases[i]) for t in r["title"])
    }
    print(f"dropped for combined-index ambiguity: {len(cases) - len(kept_idx)}")

    out = SYN / "splits"
    for name in FRACTIONS:
        for task in TASKS:
            rows_out = [c for i, c in enumerate(cases)
                        if i in kept_idx and split_of[i] == name and c["meta"]["task"] == task]
            path = out / name / f"{task}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows_out), encoding="utf-8")
            print(f"{name:8s} {task:8s} {len(rows_out)}")

    docs = SYN / "search-documents.jsonl"
    with docs.open("w", encoding="utf-8", newline="\n") as dst:
        for pid in sorted(lines, key=lambda p: chosen[p]):
            dst.write(lines[pid][1] + "\n")
    print(f"documents: {len(lines)} -> {docs}")


if __name__ == "__main__":
    main()
