from pathlib import Path

from constants import PAPERS_COLLECTION_NAME
from rag.pipeline import build_collection_from_path, search_collection


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_FOLDER = PROJECT_ROOT / "resources"
COLLECTION_NAME = PAPERS_COLLECTION_NAME


def main():
    build_result = build_collection_from_path(
        path=RESOURCE_FOLDER,
        collection_name=COLLECTION_NAME,
    )

    print("Documents loaded:", build_result["documents_loaded"])
    print("Chunks added:", build_result["chunks_added"])
    print("Collection count:", build_result["collection_count"])

    results = search_collection(
        collection_name=COLLECTION_NAME,
        query="How does row spacing affect bifacial solar farm yield?",
        n_results=5,
    )

    for result in results:
        metadata = result["metadata"]
        print("-" * 80)
        print("Title:", metadata["title"])
        print("Page:", metadata["page"])
        print("Headings:", metadata["headings"])
        print("Distance:", result["distance"])
        print(result["text"][:800])


if __name__ == "__main__":
    main()
