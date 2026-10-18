from pathlib import Path
import re

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from constants import DATA_DIR
from rag.equations import equation_intent, equation_signals


DEFAULT_CHROMA_DB_PATH = DATA_DIR / "chroma_db"

_QUERY_STOP_WORDS = {
    "about", "and", "define", "defines", "does", "equation", "formula", "from",
    "give", "gives", "into", "relate", "relates", "show", "shows", "that",
    "the", "this", "using", "what", "which", "with",
}


def get_chroma_client(db_path=DEFAULT_CHROMA_DB_PATH):
    return chromadb.PersistentClient(path=str(db_path))

def get_or_create_collection(client, collection_name):
    return client.get_or_create_collection(name=collection_name, embedding_function=DefaultEmbeddingFunction()) 

def clean_metadata(chunk):
    """
    Convert chunk metadata into Chroma-compatible metadata.

    Chroma metadata values must be str, int, float, bool, or None-like avoided.
    Lists are not allowed.
    """
    headings = chunk.get("headings", [])

    metadata = {
        "page": chunk["page"] if chunk.get("page") is not None else -1,
        "chunk_index": chunk["chunk_index"],
        "equation_index": int(chunk.get("equation_index", -1)),
        "source": chunk["source"],
        "title": chunk["title"],
        "headings": " > ".join(headings) if headings else "",
        "chunk_type": "docling",
        "record_type": chunk.get("record_type", "context"),
        "has_equation": bool(chunk.get("has_equation", False)),
        "equation_count": int(chunk.get("equation_count", 0)),
        "ingestion_profile": chunk.get("ingestion_profile", "standard"),
    }
    if chunk.get("equation_latex"):
        metadata["equation_latex"] = chunk["equation_latex"]
    if chunk.get("parent_record_key"):
        metadata["parent_id"] = create_record_id(
            chunk["source"], chunk["parent_record_key"]
        )
    return metadata

def add_chunks_to_collection(collection, chunks, upsert=False):
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [clean_metadata(chunk) for chunk in chunks]
    ids = [
        create_chunk_id(chunk)
        for chunk in chunks
    ]

    write = collection.upsert if upsert else collection.add
    write(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )


def create_record_id(source, record_key):
    source_stem = Path(source).stem
    safe_source = "".join(
        character if character.isalnum() else "_"
        for character in source_stem
    )
    return f"{safe_source}_{record_key}"


def create_chunk_id(chunk):
    record_key = chunk.get("record_key", f"chunk_{chunk['chunk_index']}")
    return create_record_id(chunk["source"], record_key)


def query_collection(collection, query_text, n_results=5):
    collection_count = collection.count()
    if collection_count == 0:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
    results = collection.query(
        query_texts=[query_text],
        n_results=min(n_results, collection_count),
    )
    return results

def format_query_results(results):
    """
    Convert Chroma's nested result format into a cleaner list of dictionaries.
    """
    formatted_results = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    for document, metadata, distance, result_id in zip(
        documents,
        metadatas,
        distances,
        ids,
    ):
        formatted_results.append({
            "id": result_id,
            "text": document,
            "metadata": metadata,
            "distance": distance,
        })

    return formatted_results


def rerank_equation_results(results, query_text, n_results=5):
    """Prefer equation-bearing candidates only when the question asks for math."""
    if not equation_intent(query_text):
        return results[:n_results]

    candidate_count = max(len(results), 1)
    query_terms = {
        term for term in re.findall(r"[a-z0-9]+", str(query_text).casefold())
        if len(term) >= 3 and term not in _QUERY_STOP_WORDS
    }
    reranked = []
    for original_rank, result in enumerate(results, start=1):
        metadata = result.get("metadata", {})
        has_equation = bool(metadata.get("has_equation"))
        if not has_equation:
            has_equation = equation_signals(result.get("text"))["has_equation"]
        rank_score = 1 - ((original_rank - 1) / candidate_count)
        record_type = metadata.get("record_type")
        equation_bonus = 0.7 if record_type == "equation" else (0.15 if has_equation else 0)
        compact_text = re.sub(r"[^a-z0-9]", "", str(result.get("text", "")).casefold())
        term_overlap = (
            sum(term in compact_text for term in query_terms) / len(query_terms)
            if query_terms else 0
        )
        lexical_bonus = 0.6 * term_overlap
        score = rank_score + equation_bonus + lexical_bonus
        enriched = dict(result)
        enriched["original_rank"] = original_rank
        enriched["equation_term_overlap"] = round(term_overlap, 6)
        enriched["equation_rerank_score"] = round(score, 6)
        reranked.append(enriched)

    reranked.sort(key=lambda item: item["equation_rerank_score"], reverse=True)
    return reranked[:n_results]


def attach_parent_context(collection, results):
    """Attach linked explanatory chunks to retrieved equation records."""
    parent_ids = {
        result.get("metadata", {}).get("parent_id")
        for result in results
        if result.get("metadata", {}).get("record_type") == "equation"
        and result.get("metadata", {}).get("parent_id")
    }
    if not parent_ids:
        return results

    records = collection.get(
        ids=sorted(parent_ids),
        include=["documents", "metadatas"],
    )
    parents = {
        record_id: {"id": record_id, "text": document, "metadata": metadata}
        for record_id, document, metadata in zip(
            records.get("ids", []),
            records.get("documents", []),
            records.get("metadatas", []),
        )
    }
    enriched = []
    for result in results:
        item = dict(result)
        parent_id = item.get("metadata", {}).get("parent_id")
        if parent_id in parents:
            item["parent_context"] = parents[parent_id]
        enriched.append(item)
    return enriched
