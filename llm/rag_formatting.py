from rag.source_titles import display_source_title


def format_retrieved_context(retrieved_context):
    """
    Format a list of retrieved RAG chunks (as returned by rag.pipeline.retrieve_for_source)
    into numbered excerpt blocks with title/page, for dropping into a prompt.

    Returns None if there's nothing to format, so each caller can decide how to
    represent "no context" in its own prompt structure (omit the section entirely,
    or show a "None available." placeholder).
    """
    if not retrieved_context:
        return None

    context_blocks = []
    for index, chunk in enumerate(retrieved_context, start=1):
        metadata = chunk.get("metadata", {})
        title = display_source_title(metadata.get("title"))
        if metadata.get("library"):
            title = f"{metadata['library']}: {title}"
        page = metadata.get("page", "unknown page")
        context_blocks.append(f"Excerpt {index} ({title}, page {page}):\n{chunk['text']}")

    return "\n---\n".join(context_blocks)
