import argparse
import csv
import getpass
import json
import os
import time
from difflib import SequenceMatcher
from pathlib import Path

from dotenv import load_dotenv

from constants import RAG_SOURCE_NONE, RAG_SOURCES
from llm.client import DEFAULT_MODEL
from llm.general_agpv_answerer import answer_general_agpv_question
from llm.rag_pair_evaluator import evaluate_answer_pair
from llm.rag_source_router import decide_rag_source
from rag.pipeline import retrieve_for_source


OUTPUT_FIELDS = [
    "case_id", "session_id", "timestamp", "question", "user_profile",
    "location_context", "conversation_history", "model_name",
    "retrieval_source", "router_reason", "retrieval_query",
    "retrieved_count", "retrieved_chunks", "no_rag_answer", "rag_answer",
    "no_rag_response_time_ms", "rag_response_time_ms",
    "answer_similarity_ratio", "evaluation_status",
    "judge_preferred_answer", "judge_no_rag_correctness",
    "judge_rag_correctness", "judge_no_rag_relevance",
    "judge_rag_relevance", "judge_no_rag_usefulness",
    "judge_rag_usefulness", "judge_no_rag_profile_adaptation",
    "judge_rag_profile_adaptation", "judge_rag_evidence_support",
    "judge_no_rag_unsupported_claims", "judge_rag_unsupported_claims",
    "judge_reason", "judge_raw_result",
    "human_no_rag_correctness", "human_rag_correctness",
    "human_rag_groundedness", "human_no_rag_usefulness",
    "human_rag_usefulness", "human_preferred_answer",
    "human_unsupported_claims", "human_notes",
]


def _json_value(value, fallback):
    if isinstance(value, (dict, list)):
        return value
    if not value:
        return fallback
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback
    return parsed


def _is_selected(value):
    return str(value).strip().lower() in {"1", "true", "yes", "y", "include"}


def _eligible(row):
    return (
        bool((row.get("question") or "").strip())
        and row.get("turn_type") == "general_question"
        and not (row.get("error") or "").strip()
    )


def select_case_indices(rows, limit):
    explicitly_selected = [
        index for index, row in enumerate(rows)
        if _eligible(row) and _is_selected(row.get("include_for_evaluation"))
    ]
    candidates = explicitly_selected or [
        index for index, row in enumerate(rows) if _eligible(row)
    ]

    selected = []
    seen_questions = set()
    for index in candidates:
        normalized_question = " ".join(rows[index]["question"].lower().split())
        if normalized_question in seen_questions:
            continue
        seen_questions.add(normalized_question)
        selected.append(index)
        if len(selected) >= limit:
            break
    return selected


def histories_before_each_row(rows):
    histories = []
    by_session = {}
    for row in rows:
        session_id = row.get("session_id") or "unknown-session"
        history = by_session.setdefault(session_id, [])
        histories.append(list(history))
        question = (row.get("question") or "").strip()
        answer = (row.get("answer") or "").strip()
        if question:
            history.append({"role": "user", "content": question})
        if answer:
            history.append({"role": "assistant", "content": answer})
    return histories


def _source_for_case(row, question, history, api_key):
    expected = (row.get("expected_sources") or "").strip().lower()
    recorded = (row.get("rag_source") or "").strip().lower()
    if expected in RAG_SOURCES and expected != RAG_SOURCE_NONE:
        return expected, "Source selected by the evaluation dataset."
    if recorded in RAG_SOURCES and recorded != RAG_SOURCE_NONE:
        return recorded, row.get("rag_router_reason") or "Recorded app route."
    plan = decide_rag_source(question, api_key, conversation_history=history)
    return plan["source"], plan.get("reason")


def _chunk_export(chunks):
    exported = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        exported.append({
            "title": metadata.get("title"),
            "page": metadata.get("page"),
            "headings": metadata.get("headings"),
            "distance": chunk.get("distance"),
            "text": chunk.get("text"),
        })
    return exported


def _timed_answer(**kwargs):
    started = time.perf_counter()
    answer = answer_general_agpv_question(**kwargs)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    return answer, elapsed_ms


def run_case(row, history, api_key, model, run_judge, case_number):
    question = row["question"].strip()
    profile = _json_value(row.get("user_profile"), {})
    location = _json_value(row.get("location_context"), {})
    source, router_reason = _source_for_case(row, question, history, api_key)
    chunks = retrieve_for_source(source, question) if source != RAG_SOURCE_NONE else []

    shared = {
        "user_question": question,
        "api_key": api_key,
        "user_profile": profile,
        "location_context": location,
        "conversation_history": history,
        "model": model,
        "temperature": 0,
    }
    no_rag_answer, no_rag_ms = _timed_answer(**shared, retrieved_context=[])
    rag_answer, rag_ms = _timed_answer(**shared, retrieved_context=chunks)

    judge_result = {}
    if run_judge:
        judge_result = evaluate_answer_pair(
            question, no_rag_answer, rag_answer, chunks, api_key,
            user_profile=profile, model=model,
        )

    no_rag_scores = judge_result.get("no_rag", {})
    rag_scores = judge_result.get("rag", {})

    return {
        "case_id": f"case_{case_number:03d}",
        "session_id": row.get("session_id", ""),
        "timestamp": row.get("timestamp", ""),
        "question": question,
        "user_profile": json.dumps(profile, ensure_ascii=False),
        "location_context": json.dumps(location, ensure_ascii=False),
        "conversation_history": json.dumps(history, ensure_ascii=False),
        "model_name": model,
        "retrieval_source": source,
        "router_reason": router_reason or "",
        "retrieval_query": question,
        "retrieved_count": len(chunks),
        "retrieved_chunks": json.dumps(_chunk_export(chunks), ensure_ascii=False),
        "no_rag_answer": no_rag_answer,
        "rag_answer": rag_answer,
        "no_rag_response_time_ms": no_rag_ms,
        "rag_response_time_ms": rag_ms,
        "answer_similarity_ratio": round(
            SequenceMatcher(None, no_rag_answer, rag_answer).ratio(), 4
        ),
        "evaluation_status": "ready_for_review" if chunks else "no_context_retrieved",
        "judge_preferred_answer": judge_result.get("preferred_answer", ""),
        "judge_no_rag_correctness": no_rag_scores.get("correctness", ""),
        "judge_rag_correctness": rag_scores.get("correctness", ""),
        "judge_no_rag_relevance": no_rag_scores.get("relevance", ""),
        "judge_rag_relevance": rag_scores.get("relevance", ""),
        "judge_no_rag_usefulness": no_rag_scores.get("practical_usefulness", ""),
        "judge_rag_usefulness": rag_scores.get("practical_usefulness", ""),
        "judge_no_rag_profile_adaptation": no_rag_scores.get("profile_adaptation", ""),
        "judge_rag_profile_adaptation": rag_scores.get("profile_adaptation", ""),
        "judge_rag_evidence_support": rag_scores.get("evidence_support", ""),
        "judge_no_rag_unsupported_claims": json.dumps(
            no_rag_scores.get("unsupported_claims", []), ensure_ascii=False
        ) if judge_result else "",
        "judge_rag_unsupported_claims": json.dumps(
            rag_scores.get("unsupported_claims", []), ensure_ascii=False
        ) if judge_result else "",
        "judge_reason": judge_result.get("reason", ""),
        "judge_raw_result": json.dumps(judge_result, ensure_ascii=False) if judge_result else "",
        "human_no_rag_correctness": "",
        "human_rag_correctness": "",
        "human_rag_groundedness": "",
        "human_no_rag_usefulness": "",
        "human_rag_usefulness": "",
        "human_preferred_answer": "",
        "human_unsupported_claims": "",
        "human_notes": "",
    }


def run_evaluation(input_path, output_path, api_key, limit=20, model=DEFAULT_MODEL, run_judge=False):
    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))

    selected_indices = select_case_indices(rows, limit)
    histories = histories_before_each_row(rows)
    output_rows = []
    for case_number, row_index in enumerate(selected_indices, start=1):
        print(f"Running paired evaluation {case_number}/{len(selected_indices)}")
        try:
            result = run_case(
                rows[row_index], histories[row_index], api_key, model,
                run_judge, case_number,
            )
        except Exception as error:
            result = {field: "" for field in OUTPUT_FIELDS}
            result.update({
                "case_id": f"case_{case_number:03d}",
                "session_id": rows[row_index].get("session_id", ""),
                "timestamp": rows[row_index].get("timestamp", ""),
                "question": rows[row_index].get("question", ""),
                "model_name": model,
                "evaluation_status": f"failed: {error}",
            })
        output_rows.append(result)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8-sig", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
            writer.writeheader()
            writer.writerows(output_rows)
    return len(output_rows)


def main():
    parser = argparse.ArgumentParser(
        description="Generate matched RAG-on/RAG-off answers from conversation logs."
    )
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--judge", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("PURDUE_GENAI_KEY")
    if not api_key:
        api_key = getpass.getpass("Enter your Purdue GenAI API key: ").strip()
    if not api_key:
        raise ValueError("A Purdue GenAI API key is required.")

    count = run_evaluation(
        args.input_csv,
        args.output_csv,
        api_key,
        limit=args.limit,
        model=args.model,
        run_judge=args.judge,
    )
    print(f"Wrote {count} paired evaluations to {args.output_csv}")


if __name__ == "__main__":
    main()
