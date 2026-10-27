"""Wire validated synthetic splits into the evaluation lifecycle and RFT data formats.

Splits (data/synthetic/splits): train -> training pool, val -> development, heldout -> final test.
Compound cases are graded as voucher tasks and keep `variant: "compound"`.
RFT validation rows are drawn from the training pool, so dev and final stay disjoint.

Outputs:
  evals/datasets/synthetic/{training,development,final}/{task}.jsonl
  evals/datasets/synthetic/optimization/{task}-round{1,2}.jsonl
  evals/datasets/synthetic/manifest.json
  rft/data/synthetic/{task}-{train,validation,validation-eval,calibration-eval}.jsonl

RFT rows embed the developer message from agents/<graded task>/<--stage>. Regenerate after
Agent Optimizer retains a configuration, with --stage optimized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from rft.scripts.prepare_data import CALIBRATION_ROLLOUTS, _rft_item
from shoppingbench_foundry.benchmark_subset import _criteria

SYN = ROOT / "data" / "synthetic" / "splits"
TASKS = ("product", "shop", "voucher", "compound")
SPLIT_DIRS = {"train": "training", "val": "development", "heldout": "final"}
OPT_ROUND1, OPT_ROUND2, RFT_VALIDATION_GROUPS = 20, 40, 20


def graded(task: str) -> str:
    return "voucher" if task == "compound" else task


def developer_message(stage: str, task: str) -> str:
    config = ROOT / "agents" / graded(task) / stage
    parts = [(config / "instructions.md").read_text(encoding="utf-8").strip()]
    parts += [p.read_text(encoding="utf-8").strip() for p in sorted(config.glob("skills/*/SKILL.md"))]
    return "\n\n".join(parts)


def write(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    path.write_text(body, encoding="utf-8", newline="\n")
    return hashlib.sha256(body.encode()).hexdigest()


def lifecycle_row(task: str, name: str, case: dict) -> dict:
    item = {k: v for k, v in case.items() if k != "meta"}
    item.update(task=graded(task), variant=task, group=case["meta"]["group"])
    return {"name": name, "query": case["query"], "criteria": _criteria(graded(task), item), "item": item}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="baseline", choices=["baseline", "optimized"])
    args = ap.parse_args()
    out_eval = ROOT / "evals" / "datasets" / "synthetic"
    out_rft = ROOT / "rft" / "data" / "synthetic"
    manifest: dict = {"schema_version": 1, "stage": args.stage, "files": {}, "counts": {}}
    for task in TASKS:
        rows_by_split: dict[str, list[dict]] = {}
        for split, folder in SPLIT_DIRS.items():
            cases = [json.loads(x) for x in (SYN / split / f"{task}.jsonl").read_text("utf-8").split("\n") if x]
            rows = [lifecycle_row(task, f"syn-{task}-{split}-{i:04d}", c) for i, c in enumerate(cases)]
            rows_by_split[split] = rows
            path = out_eval / folder / f"{task}.jsonl"
            manifest["files"][path.relative_to(ROOT).as_posix()] = write(path, rows)
            manifest["counts"][f"{task}/{folder}"] = len(rows)
        train = list(rows_by_split["train"])
        random.Random(f"synthetic-{task}-optimizer").shuffle(train)
        for label, chunk in (("round1", train[:OPT_ROUND1]), ("round2", train[OPT_ROUND1:OPT_ROUND1 + OPT_ROUND2])):
            path = out_eval / "optimization" / f"{task}-{label}.jsonl"
            manifest["files"][path.relative_to(ROOT).as_posix()] = write(path, chunk)
            manifest["counts"][f"{task}/optimization-{label}"] = len(chunk)

        groups: dict[str, list[dict]] = defaultdict(list)
        for row in rows_by_split["train"]:
            groups[row["item"]["group"]].append(row)
        ordered = list(groups.values())
        random.Random(f"synthetic-rft-{task}").shuffle(ordered)
        validation = [r for g in ordered[:RFT_VALIDATION_GROUPS] for r in g]
        training = [r for g in ordered[RFT_VALIDATION_GROUPS:] for r in g]
        message = developer_message(args.stage, task)

        def rft(row: dict, message: str = message, task: str = task) -> dict:
            item = _rft_item(graded(task), row["name"], row["item"], message, f"syn-group-{row['item']['group']}")
            item["variant"] = task
            return item

        outputs = {
            "train": [rft(r) for r in training],
            "validation": [rft(r) for r in validation],
            "validation-eval": [{"name": r["name"], "query": r["query"], "item": rft(r)} for r in validation],
            "calibration-eval": [
                {"name": f"{r['name']}-rollout-{n}", "query": r["query"], "item": rft(r)}
                for r in validation for n in range(1, CALIBRATION_ROLLOUTS + 1)
            ],
        }
        for suffix, rows in outputs.items():
            path = out_rft / f"{task}-{suffix}.jsonl"
            manifest["files"][path.relative_to(ROOT).as_posix()] = write(path, rows)
            manifest["counts"][f"{task}/rft-{suffix}"] = len(rows)
        manifest.setdefault("developer_message_sha256", {})[task] = hashlib.sha256(message.encode()).hexdigest()
    (out_eval / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=1))


if __name__ == "__main__":
    main()
