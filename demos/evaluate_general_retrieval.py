"""Evaluate non-equation research retrieval against verified source titles."""

import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from constants import PAPERS_COLLECTION_NAME
from rag.pipeline import search_collection_adaptive


OUTPUT_FIELDS = [
    "case_id",
    "concept",
    "question",
    "expected_title_contains",
    "source_hit_at_k",
    "first_relevant_rank",
    "latency_ms",
    "retrieved_titles",
    "retrieved_pages",
    "error",
]


def split_expected_titles(value):
    return [part.strip() for part in (value or "").split("|") if part.strip()]


def first_expected_title_rank(titles, expected_titles):
    expected = [value.casefold() for value in expected_titles]
    for rank, title in enumerate(titles, start=1):
        normalized = (title or "").casefold()
        if any(value in normalized for value in expected):
            return rank
    return None


def summarize_rows(rows):
    successful = [row for row in rows if not row["error"]]
    ranks = [row["first_relevant_rank"] for row in successful if row["first_relevant_rank"]]
    latencies = [row["latency_ms"] for row in successful]
    return {
        "cases": len(rows),
        "successful_queries": len(successful),
        "source_hit_at_k": round(len(ranks) / len(successful), 4) if successful else 0,
        "mean_first_relevant_rank": round(statistics.mean(ranks), 2) if ranks else None,
        "median_latency_ms": round(statistics.median(latencies)) if latencies else None,
        "mean_latency_ms": round(statistics.mean(latencies)) if latencies else None,
    }


def evaluate_cases(input_path, collection_name=PAPERS_COLLECTION_NAME, k=3):
    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        cases = list(csv.DictReader(source))

    rows = []
    for case in cases:
        started = time.perf_counter()
        try:
            hits = search_collection_adaptive(
                collection_name,
                case["question"],
                n_results=k,
            )
            latency_ms = round((time.perf_counter() - started) * 1000)
            metadata = [hit.get("metadata", {}) for hit in hits]
            titles = [item.get("title", "") for item in metadata]
            pages = [item.get("page") for item in metadata]
            rank = first_expected_title_rank(
                titles,
                split_expected_titles(case["expected_title_contains"]),
            )
            error = ""
        except Exception as exc:
            latency_ms = round((time.perf_counter() - started) * 1000)
            titles = []
            pages = []
            rank = None
            error = f"{type(exc).__name__}: {exc}"

        rows.append({
            "case_id": case["case_id"],
            "concept": case["concept"],
            "question": case["question"],
            "expected_title_contains": case["expected_title_contains"],
            "source_hit_at_k": int(rank is not None),
            "first_relevant_rank": rank,
            "latency_ms": latency_ms,
            "retrieved_titles": json.dumps(titles, ensure_ascii=False),
            "retrieved_pages": json.dumps(pages, ensure_ascii=False),
            "error": error,
        })
    return rows


def write_results(output_path, rows):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=REPO_ROOT / "demos" / "general_retrieval_cases.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "outputs" / "general_retrieval_evaluation.csv",
    )
    parser.add_argument("--collection", default=PAPERS_COLLECTION_NAME)
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()

    rows = evaluate_cases(args.input, collection_name=args.collection, k=args.k)
    write_results(args.output, rows)
    print(json.dumps(summarize_rows(rows), indent=2))
    print(f"Wrote {len(rows)} cases to {args.output}")


if __name__ == "__main__":
    main()
