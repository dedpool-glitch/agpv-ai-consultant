import argparse
import csv
import json
from pathlib import Path


LOG_FIELDS = [
    "timestamp",
    "session_id",
    "mode",
    "turn_type",
    "question",
    "answer",
    "model_name",
    "user_profile",
    "location_context",
    "rag_enabled",
    "rag_source",
    "rag_router_reason",
    "retrieval_query",
    "retrieved_count",
    "retrieved_chunks",
    "response_time_ms",
    "error",
]

EVALUATION_FIELDS = [
    "include_for_evaluation",
    "question_category",
    "expected_sources",
    "retrieval_relevance_score",
    "answer_correctness_score",
    "groundedness_score",
    "citation_accuracy_score",
    "profile_adaptation_score",
    "evaluator_notes",
]


def _parse_chunks(value):
    if not value:
        return []
    try:
        chunks = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return chunks if isinstance(chunks, list) else []


def normalize_row(row):
    chunks = _parse_chunks(row.get("retrieved_chunks"))
    normalized = {field: row.get(field, "") for field in LOG_FIELDS}
    normalized["retrieved_count"] = len(chunks)
    normalized["retrieved_chunks"] = json.dumps(chunks, ensure_ascii=False)

    # Historical exports do not contain the router decision. Retrieval can
    # prove that RAG ran, but an empty result cannot prove that it was disabled.
    if not normalized["rag_enabled"] and chunks:
        normalized["rag_enabled"] = "true"
    if not normalized["rag_source"] and chunks:
        normalized["rag_source"] = "unknown"
    if not normalized["retrieval_query"] and chunks:
        normalized["retrieval_query"] = row.get("question", "")

    for field in EVALUATION_FIELDS:
        normalized[field] = row.get(field, "")
    return normalized


def prepare_dataset(input_path, output_path):
    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = [normalize_row(row) for row in csv.DictReader(source)]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=LOG_FIELDS + EVALUATION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Normalize an AgPV conversation-log CSV for RAG evaluation."
    )
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()
    count = prepare_dataset(args.input_csv, args.output_csv)
    print(f"Wrote {count} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
