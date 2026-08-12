"""
Stage 3 of RAGAS evaluation setup.

Goal: manually score one real question/answer/context triple from the actual
RAG pipeline using the Faithfulness metric, and inspect the raw result before
scaling up to the full demo question set.
"""

import demos.ragas_compat  # noqa: F401 -- must run before importing ragas

import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness

from constants import GENAI_API_KEY_ENV_VAR, PAPERS_COLLECTION_NAME
from rag.pipeline import answer_from_collection


def main():
    load_dotenv()
    api_key = os.getenv(GENAI_API_KEY_ENV_VAR)

    if not api_key:
        raise ValueError(f"{GENAI_API_KEY_ENV_VAR} is missing from the environment.")

    client = AsyncOpenAI(
        base_url="https://genai.rcac.purdue.edu/api",
        api_key=api_key,
    )
    llm = llm_factory("llama4:latest", client=client)

    question = "If I leave more space between solar panel rows, how would that affect the system?"

    result = answer_from_collection(
        collection_name=PAPERS_COLLECTION_NAME,
        question=question,
        api_key=api_key,
        n_results=3,
        user_profile={
            "user_type": "Farmer/Landowner",
            "solar_experience": "Beginner-I am new to solar farm design.",
            "project_goal": "Understand if AgPV is feasible for my land",
        },
    )

    retrieved_contexts = [chunk["text"] for chunk in result["retrieved_chunks"]]

    print("Question:", question)
    print("\nAnswer:", result["answer"])
    print(f"\nRetrieved {len(retrieved_contexts)} contexts.")

    scorer = Faithfulness(llm=llm)
    score = scorer.score(
        user_input=question,
        response=result["answer"],
        retrieved_contexts=retrieved_contexts,
    )

    print("\nFaithfulness score:", score.value)


if __name__ == "__main__":
    main()