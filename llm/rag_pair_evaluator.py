import json

from llm.client import DEFAULT_MODEL, call_llm
from llm.json_utils import parse_json_response
from llm.prompts import RAG_PAIR_EVALUATOR_SYSTEM_PROMPT
from llm.rag_formatting import format_retrieved_context


def evaluate_answer_pair(
    question,
    no_rag_answer,
    rag_answer,
    retrieved_context,
    api_key,
    user_profile=None,
    model=DEFAULT_MODEL,
):
    """Return a preliminary LLM rubric score for a paired RAG evaluation."""
    evidence = format_retrieved_context(retrieved_context) or "No excerpts were retrieved."
    messages = [
        {"role": "system", "content": RAG_PAIR_EVALUATOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Question:\n{question}\n\n"
                f"User profile:\n{json.dumps(user_profile, indent=2)}\n\n"
                f"Retrieved evidence:\n{evidence}\n\n"
                f"Answer without RAG:\n{no_rag_answer}\n\n"
                f"Answer with RAG:\n{rag_answer}\n\n"
                "Evaluate the pair."
            ),
        },
    ]
    response = call_llm(messages, api_key, model=model, temperature=0)
    result = parse_json_response(response)
    if not isinstance(result, dict):
        return {"error": "Evaluator did not return valid JSON.", "raw_response": response}
    return result
