from llm.prompts import RAG_ANSWER_SYSTEM_PROMPT
from llm.client import call_llm


def format_retrieved_context(retrieved_chunks):
    context_blocks = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        metadata = chunk["metadata"]

        title = metadata.get("title", "Unknown source")
        page = metadata.get("page", "unknown page")
        headings = metadata.get("headings", "")

        context_blocks.append(
            f"""
Source {index}
Title: {title}
Page: {page}
Headings: {headings}
Text:
{chunk["text"]}
"""
        )

    return "\n---\n".join(context_blocks)


def answer_with_rag(question, retrieved_chunks, api_key, user_profile=None):
    context = format_retrieved_context(retrieved_chunks)

    messages = [
        {
            "role": "system",
            "content": RAG_ANSWER_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": f"""
User profile:
{user_profile}

Question:
{question}

Retrieved source excerpts:
{context}

Answer the question using only the retrieved source excerpts.
""",
        },
    ]

    return call_llm(messages, api_key)
