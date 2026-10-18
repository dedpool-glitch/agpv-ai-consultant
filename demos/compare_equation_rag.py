"""Compare standard and equation-aware RAG on the same equation questions.

The input CSV requires ``question``. Optional reference columns are ``case_id``,
``expected_terms`` (pipe-separated), ``expected_title_contains``, and
``expected_page``. Pass ``--generate-answers`` to compare LLM answers as well.
"""

import argparse
import csv
import getpass
import json
import os
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv

from rag.equations import equation_signals, expected_term_recall
from rag.pipeline import search_collection, search_collection_equation_aware
from rag.rag_answerer import answer_with_rag


OUTPUT_FIELDS = [
    "case_id", "question", "expected_terms", "expected_title_contains", "expected_page",
    "old_equation_hit_at_k", "new_equation_hit_at_k",
    "old_first_equation_rank", "new_first_equation_rank",
    "old_expected_term_recall", "new_expected_term_recall",
    "old_expected_source_hit", "new_expected_source_hit",
    "old_expected_page_hit", "new_expected_page_hit",
    "old_retrieval_ms", "new_retrieval_ms", "old_chunks", "new_chunks",
    "old_answer", "new_answer", "old_answer_has_equation", "new_answer_has_equation",
    "old_answer_expected_term_recall", "new_answer_expected_term_recall",
    "human_old_retrieval_relevance", "human_new_retrieval_relevance",
    "human_old_equation_accuracy", "human_new_equation_accuracy",
    "human_old_explanation_quality", "human_new_explanation_quality",
    "human_preferred_pipeline", "human_notes",
]


def _terms(value):
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def _has_equation(chunk):
    metadata = chunk.get("metadata", {})
    return bool(metadata.get("has_equation")) or equation_signals(chunk.get("text"))["has_equation"]


def _first_equation_rank(chunks):
    return next((rank for rank, chunk in enumerate(chunks, start=1) if _has_equation(chunk)), None)


def _joined_text(chunks):
    return "\n".join(chunk.get("text", "") for chunk in chunks)


def _expected_hits(chunks, title_fragment, page):
    title_hit = None
    page_hit = None
    if title_fragment:
        title_hit = any(
            title_fragment.casefold()
            in str(chunk.get("metadata", {}).get("title", "")).casefold()
            for chunk in chunks
        )
    if page not in (None, ""):
        page_hit = any(
            str(chunk.get("metadata", {}).get("page")) == str(page)
            for chunk in chunks
        )
    return title_hit, page_hit


def _export_chunks(chunks):
    return json.dumps(
        [
            {
                "rank": rank,
                "title": chunk.get("metadata", {}).get("title"),
                "page": chunk.get("metadata", {}).get("page"),
                "distance": chunk.get("distance"),
                "has_equation": _has_equation(chunk),
                "text": chunk.get("text"),
                "parent_context": chunk.get("parent_context", {}).get("text"),
            }
            for rank, chunk in enumerate(chunks, start=1)
        ],
        ensure_ascii=False,
    )


def _timed(function, *args, **kwargs):
    started = time.perf_counter()
    value = function(*args, **kwargs)
    return value, round((time.perf_counter() - started) * 1000)


def evaluate_case(row, old_collection, new_collection, top_k, api_key=None):
    question = row["question"].strip()
    terms = _terms(row.get("expected_terms"))
    title = (row.get("expected_title_contains") or "").strip()
    page = (row.get("expected_page") or "").strip()

    old_chunks, old_ms = _timed(
        search_collection, old_collection, question, n_results=top_k,
    )
    new_chunks, new_ms = _timed(
        search_collection_equation_aware,
        new_collection,
        question,
        n_results=top_k,
        candidate_count=max(20, top_k),
    )
    old_rank = _first_equation_rank(old_chunks)
    new_rank = _first_equation_rank(new_chunks)
    old_title_hit, old_page_hit = _expected_hits(old_chunks, title, page)
    new_title_hit, new_page_hit = _expected_hits(new_chunks, title, page)

    old_answer = answer_with_rag(question, old_chunks, api_key) if api_key else ""
    new_answer = answer_with_rag(question, new_chunks, api_key) if api_key else ""

    return {
        "case_id": row.get("case_id") or "",
        "question": question,
        "expected_terms": "|".join(terms),
        "expected_title_contains": title,
        "expected_page": page,
        "old_equation_hit_at_k": old_rank is not None,
        "new_equation_hit_at_k": new_rank is not None,
        "old_first_equation_rank": old_rank or "",
        "new_first_equation_rank": new_rank or "",
        "old_expected_term_recall": expected_term_recall(_joined_text(old_chunks), terms),
        "new_expected_term_recall": expected_term_recall(_joined_text(new_chunks), terms),
        "old_expected_source_hit": old_title_hit,
        "new_expected_source_hit": new_title_hit,
        "old_expected_page_hit": old_page_hit,
        "new_expected_page_hit": new_page_hit,
        "old_retrieval_ms": old_ms,
        "new_retrieval_ms": new_ms,
        "old_chunks": _export_chunks(old_chunks),
        "new_chunks": _export_chunks(new_chunks),
        "old_answer": old_answer,
        "new_answer": new_answer,
        "old_answer_has_equation": equation_signals(old_answer)["has_equation"] if old_answer else "",
        "new_answer_has_equation": equation_signals(new_answer)["has_equation"] if new_answer else "",
        "old_answer_expected_term_recall": expected_term_recall(old_answer, terms) if old_answer else "",
        "new_answer_expected_term_recall": expected_term_recall(new_answer, terms) if new_answer else "",
        "human_old_retrieval_relevance": "",
        "human_new_retrieval_relevance": "",
        "human_old_equation_accuracy": "",
        "human_new_equation_accuracy": "",
        "human_old_explanation_quality": "",
        "human_new_explanation_quality": "",
        "human_preferred_pipeline": "",
        "human_notes": "",
    }


def _mean_boolean(rows, field):
    return statistics.mean(1 if row[field] else 0 for row in rows) if rows else 0


def run_comparison(input_path, output_path, old_collection, new_collection, top_k=5, api_key=None):
    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        cases = [row for row in csv.DictReader(source) if (row.get("question") or "").strip()]

    results = []
    for index, row in enumerate(cases, start=1):
        print(f"Evaluating equation case {index}/{len(cases)}")
        result = evaluate_case(row, old_collection, new_collection, top_k, api_key=api_key)
        result["case_id"] = result["case_id"] or f"equation_{index:03d}"
        results.append(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(results)

    print(f"Old equation hit@{top_k}: {_mean_boolean(results, 'old_equation_hit_at_k'):.1%}")
    print(f"New equation hit@{top_k}: {_mean_boolean(results, 'new_equation_hit_at_k'):.1%}")
    print(f"Wrote {len(results)} comparisons to {output_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--old-collection", default="ceed_group_papers")
    parser.add_argument("--new-collection", default="ceed_group_papers_equations_v1")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--generate-answers", action="store_true")
    args = parser.parse_args()

    api_key = None
    if args.generate_answers:
        load_dotenv()
        api_key = os.getenv("PURDUE_GENAI_KEY") or getpass.getpass(
            "Enter your Purdue GenAI API key: "
        ).strip()
        if not api_key:
            raise ValueError("A Purdue GenAI API key is required to generate answers.")

    run_comparison(
        args.input_csv,
        args.output_csv,
        args.old_collection,
        args.new_collection,
        top_k=args.top_k,
        api_key=api_key,
    )


if __name__ == "__main__":
    main()
