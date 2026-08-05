"""
Ingest a folder of PDFs into a ChromaDB collection.

Reusable for any folder/collection pair -- not tied to one specific dataset.
Thin CLI wrapper around build_collection_from_path; no new ingestion logic
lives here.

Usage:
    python -m rag.ingest <folder> <collection_name>

Examples:
    python -m rag.ingest books ceed_group_books
    python -m rag.ingest papers ceed_group_papers
"""

import sys

from rag.pipeline import build_collection_from_path


def main():
    if len(sys.argv) != 3:
        print("Usage: python -m rag.ingest <folder> <collection_name>")
        sys.exit(1)

    folder, collection_name = sys.argv[1], sys.argv[2]

    print(f"Ingesting PDFs from '{folder}' into collection '{collection_name}'...")
    stats = build_collection_from_path(folder, collection_name)

    print("\nDone.")
    print(f"Documents loaded: {stats['documents_loaded']}")
    print(f"Chunks added: {stats['chunks_added']}")
    print(f"Collection count: {stats['collection_count']}")


if __name__ == "__main__":
    main()
