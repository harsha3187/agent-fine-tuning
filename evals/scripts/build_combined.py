"""Merge the original and synthetic lifecycle sets into combined sets for pooled reporting.

Writes evals/datasets/combined/{development,final}/{task}.jsonl and
data/combined/search-documents.jsonl (the same documents the live index serves).
Each row's item gets a `source` tag (original|synthetic) for traceability only; results
are reported on the pooled set.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "evals" / "datasets"
OUT = DATASETS / "combined"
TASKS = ("product", "shop", "voucher", "compound", "web")
SPLITS = ("development", "final")


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x.strip()]


def tagged(rows: list[dict], source: str) -> list[dict]:
    for row in rows:
        row.setdefault("item", {})["source"] = source
    return rows


def main() -> None:
    manifest: dict = {"schema_version": 1, "files": {}, "counts": {}}
    for split in SPLITS:
        for task in TASKS:
            rows = tagged(read(DATASETS / split / f"{task}.jsonl"), "original")
            rows += tagged(read(DATASETS / "synthetic" / split / f"{task}.jsonl"), "synthetic")
            if not rows:
                continue
            names = [r["name"] for r in rows]
            if len(set(names)) != len(names):
                raise ValueError(f"duplicate episode names in {split}/{task}")
            path = OUT / split / f"{task}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
            path.write_text(body, encoding="utf-8", newline="\n")
            key = path.relative_to(ROOT).as_posix()
            manifest["files"][key] = hashlib.sha256(body.encode("utf-8")).hexdigest()
            manifest["counts"][f"{split}/{task}"] = len(rows)

    docs_out = ROOT / "data" / "combined" / "search-documents.jsonl"
    docs_out.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    with docs_out.open("w", encoding="utf-8", newline="\n") as dst:
        for src in (ROOT / "data" / "prepared", ROOT / "data" / "synthetic"):
            for line in (src / "search-documents.jsonl").read_text(encoding="utf-8").split("\n"):
                if not line.strip():
                    continue
                pid = str(json.loads(line)["product"]["product_id"])
                if pid in seen:
                    raise ValueError(f"product id {pid} appears in both document sets")
                seen.add(pid)
                dst.write(line + "\n")
    manifest["documents"] = len(seen)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=1), f"\ndocuments: {len(seen)}")


if __name__ == "__main__":
    main()
