from pathlib import Path

from constants import (
    BOOKS_COLLECTION_NAME,
    PAPERS_COLLECTION_NAME,
    RAG_SOURCE_BOOKS,
    RAG_SOURCE_BOTH,
    RAG_SOURCE_NONE,
    RAG_SOURCE_PAPERS,
)
from rag.rag_answerer import answer_with_rag


def load_documents_from_path(path, equation_aware=False):
    """
    Load a single PDF or all PDFs inside a folder.
    """
    # Docling imports Transformers and Torch. Keep it out of the application
    # process until document ingestion is explicitly requested so it cannot
    # preload native libraries that conflict with MATLAB Engine.
    from rag.document_loader import load_pdf_document, load_pdfs_from_folder

    path = Path(path)

    if path.is_file() and path.suffix.lower() == ".pdf":
        return [load_pdf_document(path, equation_aware=equation_aware)]

    if path.is_dir():
        return load_pdfs_from_folder(path, equation_aware=equation_aware)

    raise ValueError("Path must be a PDF file or a folder containing PDFs.")


def chunk_loaded_documents(documents, equation_aware=False, chunker=None):
    """
    Convert loaded Docling documents into Chroma-ready chunks.
    """
    # Importing this module loads Transformers and Torch, including Intel's
    # OpenMP runtime. Retrieval does not need it, so load it only for ingestion.
    from rag.chunker import chunk_docling_document

    all_chunks = []

    for document in documents:
        chunks = chunk_docling_document(
            document["docling_document"],
            source=document["source"],
            title=document["title"],
            equation_aware=equation_aware,
            chunker=chunker,
        )
        all_chunks.extend(chunks)

    return all_chunks


def _pdf_paths(path):
    path = Path(path)
    if path.is_file() and path.suffix.lower() == ".pdf":
        return [path]
    if path.is_dir():
        return sorted(path.glob("*.pdf"))
    raise ValueError("Path must be a PDF file or a folder containing PDFs.")


def _page_ranges(pdf_path, page_batch_size):
    if not page_batch_size:
        return [None]
    from pypdf import PdfReader

    page_count = len(PdfReader(str(pdf_path)).pages)
    return [
        (start, min(start + page_batch_size - 1, page_count))
        for start in range(1, page_count + 1, page_batch_size)
    ]


def _indexed_context_pages(collection, source):
    records = collection.get(where={"source": source}, include=["metadatas"])
    return {
        metadata.get("page")
        for metadata in records.get("metadatas", [])
        if metadata.get("record_type") == "context" and metadata.get("page", -1) >= 0
    }


def _build_equation_collection(
    path,
    collection,
    page_batch_size,
):
    from rag.chunker import create_docling_chunker
    from rag.document_loader import create_document_converter, get_pdf_title
    from rag.vector_db import add_chunks_to_collection

    pdf_paths = _pdf_paths(path)
    converter = create_document_converter(equation_aware=True)
    chunker = create_docling_chunker()
    chunks_added = 0

    for document_index, pdf_path in enumerate(pdf_paths, start=1):
        source = str(pdf_path.resolve())
        indexed_pages = _indexed_context_pages(collection, source)
        ranges = _page_ranges(pdf_path, page_batch_size)
        for page_range in ranges:
            if page_range and set(range(page_range[0], page_range[1] + 1)).issubset(indexed_pages):
                print(
                    f"[{document_index}/{len(pdf_paths)}] Skipping {pdf_path.name} "
                    f"pages {page_range[0]}-{page_range[1]} (already indexed)"
                )
                continue
            page_label = "all pages" if page_range is None else f"pages {page_range[0]}-{page_range[1]}"
            print(f"[{document_index}/{len(pdf_paths)}] Processing {pdf_path.name}, {page_label}")
            kwargs = {"page_range": page_range} if page_range else {}
            result = converter.convert(str(pdf_path), **kwargs)
            documents = [{
                "docling_document": result.document,
                "title": get_pdf_title(pdf_path),
                "source": source,
            }]
            chunks = chunk_loaded_documents(
                documents,
                equation_aware=True,
                chunker=chunker,
            )
            add_chunks_to_collection(collection, chunks, upsert=True)
            chunks_added += len(chunks)
            indexed_pages.update(
                chunk["page"] for chunk in chunks
                if chunk.get("record_type") == "context" and chunk.get("page") is not None
            )
            print(f"  Stored {len(chunks)} records; collection count is {collection.count()}")

    return len(pdf_paths), chunks_added


def build_collection_from_path(
    path,
    collection_name,
    db_path=None,
    equation_aware=False,
    page_batch_size=None,
):
    """
    Build a Chroma collection from a PDF file or folder of PDFs.

    Returns the collection and basic indexing stats.
    """
    from rag.vector_db import add_chunks_to_collection, get_chroma_client, get_or_create_collection

    client = get_chroma_client(db_path=db_path) if db_path else get_chroma_client()
    collection = get_or_create_collection(client, collection_name)

    if equation_aware:
        documents_loaded, chunks_added = _build_equation_collection(
            path,
            collection,
            page_batch_size=page_batch_size,
        )
    else:
        documents = load_documents_from_path(path, equation_aware=False)
        chunks = chunk_loaded_documents(documents, equation_aware=False)
        add_chunks_to_collection(collection, chunks)
        documents_loaded = len(documents)
        chunks_added = len(chunks)

    return {
        "collection": collection,
        "documents_loaded": documents_loaded,
        "chunks_added": chunks_added,
        "collection_count": collection.count(),
    }


def get_collection(collection_name, db_path=None):
    """
    Open an existing collection by name.
    """
    from rag.vector_db import get_chroma_client, get_or_create_collection

    client = get_chroma_client(db_path=db_path) if db_path else get_chroma_client()
    return get_or_create_collection(client, collection_name)


def search_collection(collection_name, query, n_results=5, db_path=None):
    """
    Search a collection and return formatted results.
    """
    from rag.vector_db import format_query_results, query_collection

    collection = get_collection(collection_name, db_path=db_path)
    results = query_collection(
        collection,
        query_text=query,
        n_results=n_results,
    )
    return format_query_results(results)


def search_collection_equation_aware(
    collection_name,
    query,
    n_results=5,
    candidate_count=20,
    db_path=None,
):
    from rag.vector_db import (
        attach_parent_context,
        format_query_results,
        query_collection,
        rerank_equation_results,
    )

    collection = get_collection(collection_name, db_path=db_path)
    raw_results = query_collection(
        collection,
        query_text=query,
        n_results=max(n_results, candidate_count),
    )
    candidates = format_query_results(raw_results)
    reranked = rerank_equation_results(candidates, query, n_results=n_results)
    return attach_parent_context(collection, reranked)


def search_collection_adaptive(collection_name, query, n_results=5, db_path=None):
    """Search normally, adding equation reranking and parent context when needed."""
    return search_collection_equation_aware(
        collection_name=collection_name,
        query=query,
        n_results=n_results,
        db_path=db_path,
    )


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
                search_collection_adaptive(
                    collection_name,
                    query,
                    n_results=n_results,
                    db_path=db_path,
                )
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
    retrieved_chunks = search_collection_adaptive(
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
