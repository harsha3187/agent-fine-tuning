"""Group-disjoint split of synthetic cases and search-document build (targets + distractors)."""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from synthesize import CATALOG, ROOT, build_index  # noqa: E402

SYN = ROOT / "data" / "synthetic"
TASKS = ("product", "shop", "voucher", "compound")
FRACTIONS = {"train": 0.80, "val": 0.10, "heldout": 0.10}
SHOP_DISTRACTORS = 4
RANDOM_DISTRACTORS = 3


def pids(case: dict) -> list[str]:
    return [str(r["product_id"]) for r in case["reward"]] if isinstance(case["reward"], list) \
        else [str(case["reward"]["product_id"])]


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
        for line in (SYN / f"{task}.jsonl").read_text(encoding="utf-8").splitlines():
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
    out = SYN / "splits"
    for name in FRACTIONS:
        for task in TASKS:
            rows = [c for i, c in enumerate(cases) if split_of[i] == name and c["meta"]["task"] == task]
            path = out / name / f"{task}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
            print(f"{name:8s} {task:8s} {len(rows)}")

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
    docs = SYN / "search-documents.jsonl"
    with CATALOG.open("rb") as src, docs.open("w", encoding="utf-8", newline="\n") as dst:
        for off in sorted(chosen.values()):
            src.seek(off)
            dst.write(src.readline().decode("utf-8").rstrip("\n") + "\n")
    print(f"documents: {len(chosen)} -> {docs}")


if __name__ == "__main__":
    main()
