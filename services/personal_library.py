"""Local PDF library for the Windows account running AgPV Assistant."""

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path

from pypdf import PdfReader


COLLECTION_NAME = "personal_documents"
MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_PAGES = 100
CHUNK_WORDS = 180
CHUNK_OVERLAP = 30


def library_root():
    """Keep user data outside the checkout and replaceable executable folder."""
    override = os.getenv("AGPV_PERSONAL_LIBRARY_ROOT")
    if override:
        return Path(override).expanduser()
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "AgPV-Assistant" / "personal_library"
    return Path.home() / ".agpv-assistant" / "personal_library"


def has_personal_documents(root=None):
    root = Path(root) if root is not None else library_root()
    documents = root / "documents"
    return documents.is_dir() and any(documents.glob("*.pdf"))


def _collection(root, create=False):
    from rag.vector_db import get_chroma_client, get_or_create_collection

    db_path = root / "chroma"
    if not create and not db_path.exists():
        return None
    if create:
        db_path.mkdir(parents=True, exist_ok=True)
    client = get_chroma_client(db_path)
    return get_or_create_collection(client, COLLECTION_NAME)


def _pdf_chunks(pdf_bytes, title, document_id):
    if not pdf_bytes or len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError("Upload a PDF smaller than 20 MB.")
    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=False)
        page_count = len(reader.pages)
    except Exception as error:
        raise ValueError("The uploaded file could not be read as a PDF.") from error
    if not 1 <= page_count <= MAX_PAGES:
        raise ValueError("PDFs must contain between 1 and 100 pages.")

    chunks = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            words = (page.extract_text() or "").split()
        except Exception as error:
            raise ValueError(f"Could not extract text from page {page_number}.") from error
        step = CHUNK_WORDS - CHUNK_OVERLAP
        for chunk_index, start in enumerate(range(0, len(words), step)):
            text = " ".join(words[start:start + CHUNK_WORDS])
            if not text:
                continue
            chunks.append({
                "id": f"{document_id}:{page_number}:{chunk_index}",
                "text": text,
                "metadata": {
                    "document_id": document_id,
                    "title": title,
                    "source": title + ".pdf",
                    "page": page_number,
                    "library": "My library",
                    "page_count": page_count,
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                },
            })
    if not chunks:
        raise ValueError("No searchable text was found. Scanned PDFs need OCR before upload.")
    return chunks, page_count


def add_pdf(file_name, pdf_bytes, root=None):
    """Index one PDF and retain its original file; identical files are deduplicated."""
    name = Path(str(file_name or "")).name
    if not name.lower().endswith(".pdf"):
        raise ValueError("Upload a PDF file.")
    if not isinstance(pdf_bytes, bytes) or not pdf_bytes or len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError("Upload a PDF smaller than 20 MB.")
    root = Path(root) if root is not None else library_root()
    document_id = sha256(pdf_bytes).hexdigest()
    collection = _collection(root, create=True)
    existing = collection.get(where={"document_id": document_id}, limit=1)
    if existing["ids"]:
        return {"document_id": document_id, "already_present": True}
    chunks, page_count = _pdf_chunks(pdf_bytes, Path(name).stem, document_id)
    pdf_path = root / "documents" / f"{document_id}.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(pdf_bytes)
    try:
        collection.add(
            ids=[chunk["id"] for chunk in chunks],
            documents=[chunk["text"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks],
        )
    except Exception:
        collection.delete(where={"document_id": document_id})
        pdf_path.unlink(missing_ok=True)
        raise
    return {"document_id": document_id, "already_present": False,
            "page_count": page_count, "chunk_count": len(chunks)}


def list_documents(root=None):
    root = Path(root) if root is not None else library_root()
    collection = _collection(root)
    if collection is None:
        return []
    records = collection.get(include=["metadatas"])
    documents = {}
    for metadata in records.get("metadatas") or []:
        document_id = metadata.get("document_id")
        if not document_id:
            continue
        if document_id not in documents:
            documents[document_id] = {
                "document_id": document_id,
                "title": metadata.get("title") or "Untitled PDF",
                "page_count": metadata.get("page_count"),
                "uploaded_at": metadata.get("uploaded_at"),
                "chunk_count": 0,
            }
        documents[document_id]["chunk_count"] += 1
    return sorted(documents.values(), key=lambda item: item["uploaded_at"] or "", reverse=True)


def remove_document(document_id, root=None):
    root = Path(root) if root is not None else library_root()
    if not isinstance(document_id, str) or len(document_id) != 64 or any(
        character not in "0123456789abcdef" for character in document_id
    ):
        raise ValueError("Invalid document ID.")
    collection = _collection(root)
    if collection is None:
        return False
    existing = collection.get(where={"document_id": document_id}, limit=1)
    if not existing["ids"]:
        return False
    collection.delete(where={"document_id": document_id})
    (root / "documents" / f"{document_id}.pdf").unlink(missing_ok=True)
    return True


def search_documents(query, n_results=3, root=None):
    root = Path(root) if root is not None else library_root()
    collection = _collection(root)
    if collection is None or collection.count() == 0:
        return []
    from rag.vector_db import format_query_results, query_collection

    return format_query_results(query_collection(collection, query, n_results=n_results))
