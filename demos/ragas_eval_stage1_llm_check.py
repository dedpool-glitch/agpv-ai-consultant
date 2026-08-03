"""
Stage 1 of RAGAS evaluation setup.

Goal: prove that ragas's evaluator LLM (built on the `instructor` library for
structured output) can get a valid structured response back from Purdue
GenAI Studio, without misfiring into a native tool call the way our own
app's prompts did before we added the "no tools available" guard.

This does not touch any ragas metric yet -- it only exercises the exact LLM
object ragas metrics use internally, on a trivial structured-extraction task.
"""

import demos.ragas_compat  # noqa: F401 -- must run before importing ragas

import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from ragas.llms import llm_factory


class Sentiment(BaseModel):
    sentiment: str
    confidence: float


def main():
    load_dotenv()
    api_key = os.getenv("PURDUE_GENAI_KEY")

    if not api_key:
        raise ValueError("PURDUE_GENAI_KEY is missing from the environment.")

    # The OpenAI client appends "/chat/completions" to base_url itself, so
    # base_url should stop right before that segment.
    client = OpenAI(
        base_url="https://genai.rcac.purdue.edu/api",
        api_key=api_key,
    )

    llm = llm_factory("llama4:latest", client=client)

    print("Requesting a structured (Pydantic) response from llama4:latest...")

    result = llm.generate(
        "Classify the sentiment of this sentence: "
        "'The solar yield estimate came back higher than expected.'",
        response_model=Sentiment,
    )

    print("\nResult:")
    print(result)
    print(f"\nType: {type(result)}")


if __name__ == "__main__":
    main()