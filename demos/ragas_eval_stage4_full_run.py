"""
Stage 4 of RAGAS evaluation setup.

Runs all three reference-free metrics (Faithfulness, AnswerRelevancy,
ContextUtilization) over the same 6 questions used in rag_answer_demo.py,
and writes the scores to CSV alongside the question/answer, the same way
rag_answer_demo_results.csv already records answers and sources.
"""

import csv
import os
from pathlib import Path

import demos.ragas_compat  # noqa: F401 -- must run before importing ragas

from dotenv import load_dotenv
from openai import AsyncOpenAI

from ragas.embeddings.base import embedding_factory
from ragas.llms import llm_factory
from ragas.metrics.collections import AnswerRelevancy, ContextUtilization, Faithfulness

from demos.rag_answer_demo import RAG_DEMO_CASES
from rag.pipeline import answer_from_collection

COLLECTION_NAME = "ceed_group_papers"
OUTPUT_PATH = Path(r"D:\agpv-ai-consultant\outputs\ragas_eval_results.csv")


def build_scorers(api_key):
    client = AsyncOpenAI(
        base_url="https://genai.rcac.purdue.edu/api",
        api_key=api_key,
    )
    llm = llm_factory("llama4:latest", client=client)
    embeddings = embedding_factory(
        "huggingface",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    return {
        "faithfulness": Faithfulness(llm=llm),
        "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=embeddings),
        "context_utilization": ContextUtilization(llm=llm),
    }


def run_eval(api_key):
    scorers = build_scorers(api_key)
    rows = []

    for demo_case in RAG_DEMO_CASES:
        print(f"Running case: {demo_case['case_id']}")

        result = answer_from_collection(
            collection_name=COLLECTION_NAME,
            question=demo_case["question"],
            api_key=api_key,
            n_results=3,
            user_profile=demo_case["user_profile"],
        )

        answer = result["answer"]
        retrieved_contexts = [chunk["text"] for chunk in result["retrieved_chunks"]]

        faithfulness = scorers["faithfulness"].score(
            user_input=demo_case["question"],
            response=answer,
            retrieved_contexts=retrieved_contexts,
        )
        answer_relevancy = scorers["answer_relevancy"].score(
            user_input=demo_case["question"],
            response=answer,
        )
        context_utilization = scorers["context_utilization"].score(
            user_input=demo_case["question"],
            response=answer,
            retrieved_contexts=retrieved_contexts,
        )

        rows.append({
            "case_id": demo_case["case_id"],
            "user_type": demo_case["user_profile"]["user_type"],
            "question": demo_case["question"],
            "answer": answer,
            "faithfulness": faithfulness.value,
            "answer_relevancy": answer_relevancy.value,
            "context_utilization": context_utilization.value,
        })

    return rows


def write_results(rows, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "case_id",
                "user_type",
                "question",
                "answer",
                "faithfulness",
                "answer_relevancy",
                "context_utilization",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    load_dotenv()
    api_key = os.getenv("PURDUE_GENAI_KEY")

    if not api_key:
        raise ValueError("PURDUE_GENAI_KEY is missing from the environment.")

    rows = run_eval(api_key)
    write_results(rows, OUTPUT_PATH)

    print(f"Saved RAGAS eval results to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()