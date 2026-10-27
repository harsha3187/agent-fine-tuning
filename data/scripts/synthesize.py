"""Standalone ShoppingBench-style case synthesizer (adapted from upstream run_synthesize.py).

Code samples target products and constraints, so gold labels hold by construction.
An LLM only rewrites the requirements as a natural query. Pure Python: no Pyserini.
Existing benchmark products and their shops are excluded so new cases stay disjoint.

Example:
  python data/scripts/synthesize.py --task product --total 20 --out data/synthetic/dry/product.jsonl
"""
from __future__ import annotations

import argparse
import json
import math
import pickle
import random
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data" / "full-catalog" / "documents.jsonl"
INDEX_CACHE = ROOT / "data" / "full-catalog" / "offsets.pkl"
PROMPT = ROOT / "data" / "full-catalog" / "synthesize.md"
SOURCE_DIR = ROOT / "data" / "source"

SERVICE_TEXT = {
    "official": "The product is sold through LazMall (official store).",
    "freeShipping": "The product offer with free shipping service.",
    "COD": "The product offer with cash on delivery service.",
    "flashsale": "The product is on flash sale.",
}


def build_index() -> tuple[list[tuple[str, str, int]], dict[str, list[int]]]:
    """Return (product_id, shop_id, byte offset) rows and shop -> row indexes."""
    if INDEX_CACHE.exists():
        with INDEX_CACHE.open("rb") as fh:
            return pickle.load(fh)
    rows: list[tuple[str, str, int]] = []
    shops: dict[str, list[int]] = defaultdict(list)
    with CATALOG.open("rb") as fh:
        offset = 0
        for line in fh:
            m = re.search(rb'"product_id":\s*"(\d+)",\s*"shop_id":\s*"(\d+)"', line)
            if m:
                shops[m.group(2).decode()].append(len(rows))
                rows.append((m.group(1).decode(), m.group(2).decode(), offset))
            offset += len(line)
    result = (rows, dict(shops))
    with INDEX_CACHE.open("wb") as fh:
        pickle.dump(result, fh)
    return result


def read_product(fh, offset: int) -> dict:
    fh.seek(offset)
    return json.loads(fh.readline())["product"]


def existing_product_ids() -> set[str]:
    found: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            if "product_id" in node:
                found.add(str(node["product_id"]))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for path in SOURCE_DIR.glob("*.jsonl"):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    walk(json.loads(line).get("reward"))
    return found


def sample_price(price: float, rng: random.Random):
    mode = rng.choice(["less than", "greater than", "between"])
    if int(price) < 1:
        return None, None
    if mode == "less than":
        lo, hi = 0, int(price + rng.randint(0, int(price)))
        text = f"less than `{hi}` Philippine Peso"
    elif mode == "greater than":
        lo, hi = int(price - rng.randint(0, int(price))), None
        text = f"greater than `{lo}` Philippine Peso"
    else:
        lo, hi = int(price - rng.randint(0, int(price))), int(price + rng.randint(0, int(price)))
        text = f"between `{lo}` and `{hi}` Philippine Peso"
    if lo < 0 or price <= lo or (hi is not None and price >= hi):
        return None, None
    return {mode: [lo, hi]}, f"The `price` {text}."


def target(product: dict, rng: random.Random, exclude: tuple[str, ...] = ()) -> tuple[dict, list[str]]:
    reward: dict = {"product_id": product["product_id"]}
    reqs: list[str] = []
    n = 1
    if product.get("title"):
        reward["title"] = [product["title"]]
        reqs.append(f"{n}. The `title` is `{product['title']}`.")
        n += 1
    if product.get("sku_options") and rng.random() < 0.5:
        option = rng.choice(list(product["sku_options"].values()))
        # delivery times are not user-facing constraints
        option = {k: v for k, v in option.items() if "delivery" not in k}
        if option:
            reward["sku_options"] = [option]
            for k, v in option.items():
                reqs.append(f"{n}. The `{k}` is `{v}`.")
                n += 1
    chosen = []
    for key, values in (product.get("attributes") or {}).items():
        if key and values and rng.random() < 0.5:
            value = rng.choice(values)
            chosen.append({key: [value]})
            reqs.append(f"{n}. The `{key}` is `{value}`")
            n += 1
    if chosen:
        reward["attributes"] = chosen
    services = [s for s in product.get("service", []) if s in SERVICE_TEXT and rng.random() < 0.5]
    if services:
        reward["service"] = services
        for s in services:
            reqs.append(f"{n}. {SERVICE_TEXT[s]}")
            n += 1
    if "price" not in exclude and product.get("price", 0) > 0 and rng.random() < 0.5:
        obj, text = sample_price(product["price"], rng)
        if obj:
            reward["price"] = [obj]
            reqs.append(f"{n}. {text}")
    return reward, reqs


_NUM = r"\d[\d,]*(?:\.\d+)?"
_UNIT = r"(?:Philippine\s+)?(?:pesos?|PHP)\b"


def normalize_currency(text: str) -> str:
    """Express every price in the LLM-written text as `PHP <amount>` (catalog prices are PHP)."""
    text = re.sub(rf"({_NUM})\s*(and|to|-|–)\s*({_NUM})\s*{_UNIT}", r"PHP \1 \2 PHP \3", text, flags=re.IGNORECASE)
    text = re.sub(rf"₱\s*({_NUM})", r"PHP \1", text)
    text = re.sub(rf"({_NUM})\s*{_UNIT}", r"PHP \1", text, flags=re.IGNORECASE)
    text = re.sub(rf"\bPHP\s+({_NUM})\s+(and|to)\s+(?=\d)", r"PHP \1 \2 PHP ", text)
    text = re.sub(r"\b(?:Philippine\s+)?pesos?\b", "PHP", text, flags=re.IGNORECASE)
    return re.sub(r"\bPHP(?:\s+PHP)+\b", "PHP", text)


def draw_query(client, model: str, prompt: str) -> str | None:
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], max_completion_tokens=4000
    )
    content = resp.choices[0].message.content or ""
    m = re.search(r"```json(.+?)```", content, re.DOTALL)
    try:
        return (json.loads((m.group(1) if m else content).strip()).get("query") or "").strip() or None
    except json.JSONDecodeError:
        return None


def requirements_block(reqs_list: list[list[str]]) -> str:
    if len(reqs_list) == 1:
        return "\n".join(reqs_list[0])
    return "\n\n".join(f"## Product {i + 1}\n" + "\n".join(r) for i, r in enumerate(reqs_list))


def plan_cases(task: str, total: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    rows, shops = build_index()
    blocked = existing_product_ids()
    blocked_shops = {s for pid, s, _ in rows if pid in blocked}
    eligible_shops = [s for s, ix in shops.items() if s not in blocked_shops and len(ix) >= 4]
    plans: list[dict] = []
    used_products: set[str] = set()
    used_shops: set[str] = set()
    with CATALOG.open("rb") as fh:
        while len(plans) < total:
            if task == "product":
                pid, shop, off = rows[rng.randrange(len(rows))]
                if pid in blocked or pid in used_products or shop in blocked_shops:
                    continue
                products = [read_product(fh, off)]
            else:
                voucher_type = "platform" if task == "voucher" and rng.random() < 0.5 else "shop"
                if voucher_type == "platform":
                    picks = [rows[rng.randrange(len(rows))] for _ in range(rng.randint(1, 4))]
                    if any(p[0] in blocked or p[0] in used_products or p[1] in blocked_shops for p in picks):
                        continue
                else:
                    shop = rng.choice(eligible_shops)
                    if shop in used_shops:
                        continue
                    count = rng.randint(3, 4) if task == "compound" else rng.randint(2, 4)
                    picks = [rows[i] for i in rng.sample(shops[shop], min(count, len(shops[shop])))]
                    if any(p[0] in used_products for p in picks):
                        continue
                products = [read_product(fh, p[2]) for p in picks]
            plan = build_plan(task, products, rng, locals().get("voucher_type"))
            if not plan:
                continue
            used_products.update(p["product_id"] for p in products)
            used_shops.update(p["shop_id"] for p in products)
            plans.append(plan)
    return plans


def build_plan(task: str, products: list[dict], rng: random.Random, voucher_type: str | None) -> dict | None:
    exclude = ("price",) if task in ("voucher", "compound") else ()
    rewards, reqs = zip(*(target(p, rng, exclude) for p in products))
    rewards, reqs = list(rewards), list(reqs)
    if task == "product":
        if len(reqs[0]) < 2:
            return None
        return {"reward": rewards[0], "reqs": reqs, "task_text": "a product",
                "group": products[0]["product_id"], "shop_ids": [products[0]["shop_id"]]}
    if task == "shop":
        return {"reward": rewards, "reqs": reqs, "task_text": "a shop that sells multiple products",
                "group": products[0]["shop_id"], "shop_ids": [products[0]["shop_id"]]}
    total_price = sum(p["price"] for p in products)
    if total_price < 100:
        return None
    compound = task == "compound"
    threshold = rng.randint(int(total_price * (0.6 if compound else 0.1)), int(total_price * 0.9))
    desc = ("1. The voucher only applies to the products from the same shop."
            if voucher_type == "shop" else "1. The voucher applies to all products.")
    desc += f"\n2. It is valid only when the total price of the products exceeds PHP `{threshold}`."
    if rng.random() < 0.5:
        face = rng.randint(int(threshold * 0.1), int(threshold * 0.5))
        after = total_price - face
        desc += f"\n3. It provides a fixed discount of PHP `{face}`."
        voucher = {"discount_type": "fixed", "face_value": face, "discount": None, "cap": None}
    else:
        pct = rng.randint(10, 50)
        cap = rng.randint(int(threshold * pct / 100.0), threshold)
        if cap <= threshold * pct / 100.0:
            return None
        after = max(total_price * (1 - pct / 100.0), total_price - cap)
        desc += f"\n3. It provides a percentage discount of `{pct}%` with a cap of PHP `{cap}`."
        voucher = {"discount_type": "percentage", "face_value": None, "discount": pct / 100.0, "cap": cap}
    budget = math.ceil(after) + rng.randint(0, math.ceil(after * (0.03 if compound else 0.1)))
    voucher.update({"voucher_type": voucher_type, "threshold": threshold,
                    "price_after_voucher": after, "budget": budget})
    external = f"My budget is only PHP `{budget}`, but I have a voucher with the following rules:\n{desc}"
    task_text = ("one shop that sells all of these products, so that one same-shop voucher can be used"
                 if compound else "one or more products")
    return {"reward": rewards, "reqs": reqs, "task_text": task_text, "voucher": voucher,
            "external": external, "group": products[0]["shop_id"],
            "shop_ids": sorted({p["shop_id"] for p in products})}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["product", "shop", "voucher", "compound"], required=True)
    ap.add_argument("--total", type=int, default=20)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--model", default="gpt-5.6-luna")
    ap.add_argument("--endpoint", default="https://aoptrft-foundry-eus2.openai.azure.com/openai/v1")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import OpenAI

    token = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    client = OpenAI(base_url=args.endpoint,     api_key=token, max_retries=12)
    template = PROMPT.read_text(encoding="utf-8").strip()

    plans = plan_cases(args.task, args.total, args.seed)

    def render(plan: dict) -> dict | None:
        prompt = template.replace("<|task|>", plan["task_text"]).replace(
            "<|requirements|>", requirements_block(plan["reqs"]))
        try:
            query = draw_query(client, args.model, prompt)
        except Exception as exc:  # noqa: BLE001 - skip any failed case, e.g. content filter
            print(f"skipped case: {type(exc).__name__}", file=sys.stderr)
            return None
        if not query:
            return None
        query = normalize_currency(query)
        if plan.get("external"):
            query = f"{query}\n\n{plan['external']}"
        row = {"query": query, "reward": plan["reward"],
               "meta": {"group": plan["group"], "shop_ids": plan["shop_ids"], "task": args.task}}
        if plan.get("voucher"):
            row["voucher"] = plan["voucher"]
        return row

    with ThreadPoolExecutor(args.workers) as pool:
        rows = [r for r in pool.map(render, plans) if r]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"wrote {len(rows)}/{len(plans)} {args.task} cases -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
