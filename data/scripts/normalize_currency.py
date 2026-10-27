"""One-off migration: express all prices in existing synthetic queries as PHP.

Idempotent. Rewrites data/synthetic/{task}.jsonl in place; rerun validate_synthetic.py,
split_synthetic.py and build_synthetic_lifecycle.py afterwards.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from synthesize import ROOT, normalize_currency

MARK = "\n\nMy budget is only"
TEMPLATE_AMOUNTS = (
    (r"(?<!PHP )(My budget is only )`", r"\1PHP `"),
    (r"(exceeds )`", r"\1PHP `"),
    (r"(fixed discount of )`", r"\1PHP `"),
    (r"(cap of )`", r"\1PHP `"),
)


def migrate(query: str) -> str:
    head, sep, tail = query.partition(MARK)
    head = normalize_currency(head)
    if not sep:
        return head
    tail = MARK + tail
    for pattern, repl in TEMPLATE_AMOUNTS:
        tail = re.sub(pattern, repl, tail)
    return head + tail


def main() -> None:
    changed = 0
    for task in ("product", "shop", "voucher", "compound"):
        path = ROOT / "data" / "synthetic" / f"{task}.jsonl"
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x.strip()]
        for row in rows:
            new = migrate(row["query"])
            changed += new != row["query"]
            row["query"] = new
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                        encoding="utf-8", newline="\n")
    print(f"queries changed: {changed}")


if __name__ == "__main__":
    main()
