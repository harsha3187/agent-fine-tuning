"""Validate synthetic cases: gold labels must satisfy the canonical grader and be solvable.

Reads data/synthetic/{task}.jsonl and writes data/synthetic/validated/{task}.jsonl plus
data/synthetic/validation-report.json. Optional --api-url/--api-token also checks that the
gold products are reachable through the live find_product tool.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from synthesize import CATALOG, ROOT, build_index, read_product

from shoppingbench_foundry.grading import _normalize, _voucher_match, score_product

SYN = ROOT / "data" / "synthetic"
TASKS = ("product", "shop", "voucher", "compound")
MIN_PRODUCTS = {"product": 1, "shop": 2, "voucher": 1, "compound": 3}


def rewards_of(case: dict) -> list[dict]:
    return case["reward"] if isinstance(case["reward"], list) else [case["reward"]]


def load_products(cases: list[dict]) -> dict[str, dict]:
    rows, _ = build_index()
    offsets = {pid: off for pid, _, off in rows}
    wanted = {str(r["product_id"]) for c in cases for r in rewards_of(c)}
    products = {}
    with CATALOG.open("rb") as fh:
        for pid in wanted:
            products[pid] = read_product(fh, offsets[pid])
    return products


def title_index() -> dict[str, set[str]]:
    docs = SYN / "search-documents.jsonl"
    index: dict[str, set[str]] = defaultdict(set)
    if docs.exists():
        with docs.open(encoding="utf-8") as handle:
            for line in handle:
                product = json.loads(line)["product"]
                index[_normalize(product.get("title", ""))].add(str(product["product_id"]))
    return index


def check_case(case: dict, task: str, products: dict[str, dict], titles) -> list[str]:
    problems: list[str] = []
    rewards = rewards_of(case)
    golds = [products.get(str(r["product_id"])) for r in rewards]
    if any(p is None for p in golds):
        return ["gold_product_missing"]
    ids = [str(r["product_id"]) for r in rewards]
    if len(set(ids)) != len(ids):
        problems.append("duplicate_gold_product")
    if len(rewards) < MIN_PRODUCTS[task]:
        problems.append("too_few_products")
    for product, reward in zip(golds, rewards, strict=True):
        score = score_product(product, reward)
        if score.ground_truth != 1 or score.rule != 1:
            problems.append("gold_fails_product_rule")
        twins = titles.get(_normalize(product.get("title", "")), set()) - {str(product["product_id"])}
        if twins:
            problems.append("ambiguous_duplicate_title")
    shops = {str(p.get("shop_id")) for p in golds}
    if task in ("shop", "compound") and len(shops) != 1:
        problems.append("shop_task_spans_shops")
    if task in ("voucher", "compound"):
        voucher = case.get("voucher")
        if not voucher:
            return [*problems, "voucher_missing"]
        total = sum(float(p.get("price", 0)) for p in golds)
        if voucher["voucher_type"] == "shop" and len(shops) != 1:
            problems.append("shop_voucher_spans_shops")
        if total <= voucher["budget"]:
            problems.append("voucher_not_needed")
        if total < voucher["threshold"]:
            problems.append("threshold_unreachable")
        if _voucher_match(golds, voucher) != 1:
            problems.append("gold_fails_voucher_budget")
        if abs(total - sum(float(p["price"]) for p in golds)) > 1e-9:
            problems.append("price_mismatch")
        for needle in (voucher["budget"], voucher["threshold"]):
            if f"`{needle}`" not in case["query"]:
                problems.append("voucher_terms_missing_from_query")
    return sorted(set(problems))


def reachability(cases: list[dict], products: dict[str, dict], url: str, token: str) -> dict:
    import requests

    headers = {"Authorization": f"Bearer {token}"}
    hit = total = 0
    misses = []
    for case in cases:
        for reward in rewards_of(case):
            title = reward.get("title") or [products[str(reward["product_id"])]["title"]]
            query = re.sub(r"\s+", " ", title[0])[:200]
            total += 1
            found = False
            for page in (1, 2):
                resp = requests.get(url + "/find_product", params={"q": query, "page": page},
                                    headers=headers, timeout=60)
                if str(reward["product_id"]) in resp.text:
                    found = True
                    break
            hit += found
            if not found:
                misses.append(str(reward["product_id"]))
    return {"checked": total, "reachable": hit, "misses": misses[:20]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-url")
    ap.add_argument("--api-token")
    ap.add_argument("--api-sample", type=int, default=100)
    args = ap.parse_args()
    titles = title_index()
    report: dict = {"tasks": {}}
    kept_by_task: dict[str, list[dict]] = {}
    for task in TASKS:
        cases = [json.loads(x) for x in (SYN / f"{task}.jsonl").read_text("utf-8").split("\n") if x]
        products = load_products(cases)
        reasons: Counter = Counter()
        kept = []
        for case in cases:
            problems = check_case(case, task, products, titles)
            reasons.update(problems)
            if not problems:
                kept.append(case)
        out = SYN / "validated" / f"{task}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in kept), encoding="utf-8")
        report["tasks"][task] = {"input": len(cases), "kept": len(kept), "dropped_reasons": dict(reasons)}
        kept_by_task[task] = kept
        if args.api_url:
            report["tasks"][task]["reachability"] = reachability(
                kept[: args.api_sample], products, args.api_url, args.api_token)
        print(task, report["tasks"][task])
    (SYN / "validation-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
