from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


DEFAULT_CHROMA_DB_PATH = r"D:\agpv-ai-consultant\data\chroma_db"


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

    return {
        "page": chunk["page"] if chunk.get("page") is not None else -1,
        "chunk_index": chunk["chunk_index"],
        "source": chunk["source"],
        "title": chunk["title"],
        "headings": " > ".join(headings) if headings else "",
        "chunk_type": "docling",
    }

def add_chunks_to_collection(collection, chunks):
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [clean_metadata(chunk) for chunk in chunks]
    ids = [
        create_chunk_id(chunk)
        for chunk in chunks
    ]

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )


def create_chunk_id(chunk):
    source_stem = Path(chunk["source"]).stem
    safe_source = "".join(
        character if character.isalnum() else "_"
        for character in source_stem
    )
    return f"{safe_source}_chunk_{chunk['chunk_index']}"


def query_collection(collection, query_text, n_results=5):
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
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
