"""
Stage 2 of RAGAS evaluation setup.

Goal: confirm ragas can produce embeddings using the same all-MiniLM-L6-v2
model already used by rag/vector_db.py's Chroma DefaultEmbeddingFunction.
This keeps the eval's notion of "similar text" consistent with what your
actual retrieval pipeline uses, and avoids adding a second embedding
provider (e.g. OpenAI) just for evaluation.
"""

import demos.ragas_compat  # noqa: F401 -- must run before importing ragas

from ragas.embeddings.base import embedding_factory


def main():
    embeddings = embedding_factory(
        "huggingface",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    print(f"Embeddings object type: {type(embeddings)}")

    vector = embeddings.embed_text("What is agrivoltaics?")
    print(f"Embedding length: {len(vector)}")
    print(f"First 5 values: {vector[:5]}")


if __name__ == "__main__":
    main()