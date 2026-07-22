from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

def create_docling_chunker():
    tokenizer = HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID)
    )

    return HybridChunker(tokenizer=tokenizer)

#returns an instance of HybridChunker with a HuggingFaceTokenizer using the specified embedding model.

def chunk_docling_document(docling_document, source, title):
    chunker = create_docling_chunker()
    chunk_objects = list(chunker.chunk(docling_document))
    
    chunks=[]
    for chunk_index, chunk in enumerate(chunk_objects):
        try:
            chunk_text=chunker.serialize(chunk)
        except AttributeError:
            chunk_text = chunk.text

        page_number = None
        if chunk.meta.doc_items and chunk.meta.doc_items[0].prov:
            page_number = chunk.meta.doc_items[0].prov[0].page_no

        headings=chunk.meta.headings if chunk.meta.headings else []

        if not chunk_text.strip():
            continue
        
        chunks.append({
            "page": page_number,
            "chunk_index": chunk_index,
            "text": chunk_text.strip(),
            "source": str(source),
            "title": title,
            "headings": headings,
        })
    
    return chunks
