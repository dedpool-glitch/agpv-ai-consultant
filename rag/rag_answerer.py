from llm.prompts import RAG_ANSWER_SYSTEM_PROMPT
from llm.client import call_llm


def format_retrieved_context(retrieved_chunks):
    context_blocks = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        metadata = chunk["metadata"]

        title = metadata.get("title", "Unknown source")
        page = metadata.get("page", "unknown page")
        headings = metadata.get("headings", "")
        record_type = metadata.get("record_type", "context")
        parent_context = chunk.get("parent_context")
        parent_text = parent_context.get("text", "") if parent_context else ""
        parent_block = f"Linked explanatory context:\n{parent_text}" if parent_text else ""

        context_blocks.append(
            f"""
Source {index}
Title: {title}
Page: {page}
Headings: {headings}
Record type: {record_type}
Text:
{chunk["text"]}
{parent_block}
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
