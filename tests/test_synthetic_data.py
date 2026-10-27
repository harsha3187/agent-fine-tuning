import json
from pathlib import Path

from shoppingbench_foundry.datasets import validate_synthetic_dataset

ROOT = Path(__file__).resolve().parents[1]
SYN = ROOT / "data" / "synthetic"
TASKS = ("product", "shop", "voucher", "compound")


def _rows(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x.strip()]


def _keys(rows: list[dict]) -> tuple[set[str], set[str]]:
    products, shops = set(), set()
    for row in rows:
        rewards = row["reward"] if isinstance(row["reward"], list) else [row["reward"]]
        products.update(str(r["product_id"]) for r in rewards)
        shops.update(str(s) for s in row["meta"]["shop_ids"])
    return products, shops


def test_synthetic_split_counts():
    validate_synthetic_dataset(SYN)


def test_synthetic_splits_share_no_product_or_shop():
    seen: dict[str, tuple[set[str], set[str]]] = {}
    for split in ("train", "val", "heldout"):
        rows = [r for t in TASKS for r in _rows(SYN / "splits" / split / f"{t}.jsonl")]
        seen[split] = _keys(rows)
    names = list(seen)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert not seen[a][0] & seen[b][0], f"{a}/{b} share products"
            assert not seen[a][1] & seen[b][1], f"{a}/{b} share shops"


def test_synthetic_cases_disjoint_from_sealed_benchmark_sets():
    sealed: set[str] = set()
    for folder in ("development", "final"):
        for path in (ROOT / "evals" / "datasets" / folder).glob("*.jsonl"):
            for row in _rows(path):
                reward = row["item"]["reward"]
                for r in reward if isinstance(reward, list) else [reward]:
                    sealed.add(str(r["product_id"]))
    for split in ("train", "val", "heldout"):
        for task in TASKS:
            products, _ = _keys(_rows(SYN / "splits" / split / f"{task}.jsonl"))
            assert not products & sealed


def test_rft_validation_is_disjoint_from_rft_train_and_graded_as_voucher_variant():
    base = ROOT / "rft" / "data" / "synthetic"
    for task in TASKS:
        train = {r["case_group"] for r in _rows(base / f"{task}-train.jsonl")}
        validation = _rows(base / f"{task}-validation.jsonl")
        assert train.isdisjoint({r["case_group"] for r in validation})
        assert all(r["task"] == ("voucher" if task == "compound" else task) for r in validation)
        assert all("voucher" in r for r in validation) == (task in ("voucher", "compound"))


def test_combined_index_has_no_id_conflicts_or_gold_title_twins():
    docs = SYN / "search-documents.jsonl"
    if not docs.exists():  # gitignored build artifact
        import pytest

        pytest.skip("search-documents.jsonl not built")
    from shoppingbench_foundry.grading import _normalize

    prepared = [json.loads(x)["product"] for x in
                (ROOT / "data" / "prepared" / "search-documents.jsonl").read_text("utf-8").split("\n") if x.strip()]
    synthetic = [json.loads(x)["product"] for x in docs.read_text("utf-8").split("\n") if x.strip()]
    synthetic_ids = {str(p["product_id"]) for p in synthetic}
    assert not {str(p["product_id"]) for p in prepared} & synthetic_ids
    titles: dict[str, set[str]] = {}
    for p in prepared + synthetic:
        titles.setdefault(_normalize(p["title"]), set()).add(str(p["product_id"]))
    gold_files = [SYN / "splits" / s / f"{t}.jsonl" for s in ("train", "val", "heldout") for t in TASKS]
    gold_files += [ROOT / "data" / "source" / f"{t}.jsonl" for t in ("product", "shop", "voucher")]
    for path in gold_files:
        for row in _rows(path):
            rewards = row["reward"] if isinstance(row["reward"], list) else [row["reward"]]
            for reward in rewards:
                for title in reward["title"]:
                    twins = titles.get(_normalize(title), set()) - {str(reward["product_id"])}
                    if path.parent.name == "source":  # original cases may not be polluted by new docs
                        twins &= synthetic_ids
                    assert not twins, (path.name, reward["product_id"])
