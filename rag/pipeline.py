from pathlib import Path

from constants import (
    BOOKS_COLLECTION_NAME,
    PAPERS_COLLECTION_NAME,
    RAG_SOURCE_BOOKS,
    RAG_SOURCE_BOTH,
    RAG_SOURCE_NONE,
    RAG_SOURCE_PAPERS,
)
from rag.chunker import chunk_docling_document
from rag.document_loader import load_pdf_document, load_pdfs_from_folder
from rag.rag_answerer import answer_with_rag
from rag.vector_db import (
    add_chunks_to_collection,
    format_query_results,
    get_chroma_client,
    get_or_create_collection,
    query_collection,
)


def load_documents_from_path(path):
    """
    Load a single PDF or all PDFs inside a folder.
    """
    path = Path(path)

    if path.is_file() and path.suffix.lower() == ".pdf":
        return [load_pdf_document(path)]

    if path.is_dir():
        return load_pdfs_from_folder(path)

    raise ValueError("Path must be a PDF file or a folder containing PDFs.")


def chunk_loaded_documents(documents):
    """
    Convert loaded Docling documents into Chroma-ready chunks.
    """
    all_chunks = []

    for document in documents:
        chunks = chunk_docling_document(
            document["docling_document"],
            source=document["source"],
            title=document["title"],
        )
        all_chunks.extend(chunks)

    return all_chunks


def build_collection_from_path(path, collection_name, db_path=None):
    """
    Build a Chroma collection from a PDF file or folder of PDFs.

    Returns the collection and basic indexing stats.
    """
    client = get_chroma_client(db_path=db_path) if db_path else get_chroma_client()
    collection = get_or_create_collection(client, collection_name)

    documents = load_documents_from_path(path)
    chunks = chunk_loaded_documents(documents)

    add_chunks_to_collection(collection, chunks)

    return {
        "collection": collection,
        "documents_loaded": len(documents),
        "chunks_added": len(chunks),
        "collection_count": collection.count(),
    }


def get_collection(collection_name, db_path=None):
    """
    Open an existing collection by name.
    """
    client = get_chroma_client(db_path=db_path) if db_path else get_chroma_client()
    return get_or_create_collection(client, collection_name)


def search_collection(collection_name, query, n_results=5, db_path=None):
    """
    Search a collection and return formatted results.
    """
    collection = get_collection(collection_name, db_path=db_path)
    results = query_collection(
        collection,
        query_text=query,
        n_results=n_results,
    )
    return format_query_results(results)


SOURCE_TO_COLLECTIONS = {
    RAG_SOURCE_PAPERS: [PAPERS_COLLECTION_NAME],
    RAG_SOURCE_BOOKS: [BOOKS_COLLECTION_NAME],
    RAG_SOURCE_BOTH: [PAPERS_COLLECTION_NAME, BOOKS_COLLECTION_NAME],
    RAG_SOURCE_NONE: [],
}


def retrieve_for_source(source, query, n_results=3, db_path=None):
    """
    Retrieve chunks for a "none"/"papers"/"books"/"both" source decision.

    Each collection is queried independently and failures are swallowed per
    collection, so one missing/broken collection doesn't block retrieval
    from the other, and any failure here just means less context rather
    than a broken turn.
    """
    retrieved_chunks = []

    for collection_name in SOURCE_TO_COLLECTIONS.get(source, []):
        try:
            retrieved_chunks.extend(
                search_collection(collection_name, query, n_results=n_results, db_path=db_path)
            )
        except Exception:
            continue

    return retrieved_chunks


def summarize_retrieved_chunks(retrieved_chunks):
    """
    Trace-friendly summary of retrieved chunks -- text, source, page, and
    match distance, without the raw chunk id noise.
    """
    return [
        {
            "text": chunk["text"],
            "title": chunk.get("metadata", {}).get("title"),
            "page": chunk.get("metadata", {}).get("page"),
            "distance": chunk.get("distance"),
        }
        for chunk in retrieved_chunks
    ]


def answer_from_collection(
    collection_name,
    question,
    api_key,
    n_results=5,
    db_path=None,
    user_profile=None,
):
    """
    Retrieve relevant chunks from a collection and answer using the LLM.
    """
    retrieved_chunks = search_collection(
        collection_name=collection_name,
        query=question,
        n_results=n_results,
        db_path=db_path,
    )

    answer = answer_with_rag(
        question=question,
        retrieved_chunks=retrieved_chunks,
        api_key=api_key,
        user_profile=user_profile,
    )

    return {
        "answer": answer,
        "sources": [chunk["metadata"] for chunk in retrieved_chunks],
        "retrieved_chunks": retrieved_chunks,
    }
