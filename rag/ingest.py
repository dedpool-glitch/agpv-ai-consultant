"""
Ingest a folder of PDFs into a ChromaDB collection.

Reusable for any folder/collection pair -- not tied to one specific dataset.
Thin CLI wrapper around build_collection_from_path; no new ingestion logic
lives here.

Usage:
    python -m rag.ingest <folder> <collection_name> [--equation-aware]

Examples:
    python -m rag.ingest books ceed_group_books
    python -m rag.ingest papers ceed_group_papers
"""

import argparse

from rag.pipeline import build_collection_from_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder")
    parser.add_argument("collection_name")
    parser.add_argument("--equation-aware", action="store_true")
    parser.add_argument(
        "--page-batch-size",
        type=int,
        default=25,
        help="Pages processed per resumable batch for equation-aware ingestion.",
    )
    args = parser.parse_args()

    print(f"Ingesting PDFs from '{args.folder}' into collection '{args.collection_name}'...")
    stats = build_collection_from_path(
        args.folder,
        args.collection_name,
        equation_aware=args.equation_aware,
        page_batch_size=args.page_batch_size if args.equation_aware else None,
    )

    print("\nDone.")
    print(f"Documents loaded: {stats['documents_loaded']}")
    print(f"Chunks added: {stats['chunks_added']}")
    print(f"Collection count: {stats['collection_count']}")


if __name__ == "__main__":
    main()
