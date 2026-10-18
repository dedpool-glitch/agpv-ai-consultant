import re

from docling.chunking import HybridChunker
from docling_core.types.doc import DocItemLabel
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

from rag.equations import equation_signals

EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

def create_docling_chunker():
    tokenizer = HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID)
    )

    return HybridChunker(tokenizer=tokenizer)

#returns an instance of HybridChunker with a HuggingFaceTokenizer using the specified embedding model.

def _document_formulas(docling_document):
    items = [item for item, _level in docling_document.iterate_items()]
    formulas = []
    for index, item in enumerate(items):
        if getattr(item, "label", None) != DocItemLabel.FORMULA:
            continue
        text = str(getattr(item, "text", "") or "").strip()
        if not text:
            continue
        page = item.prov[0].page_no if getattr(item, "prov", None) else None
        nearby_text = []
        for nearby_index in range(max(0, index - 2), min(len(items), index + 3)):
            nearby_item = items[nearby_index]
            if nearby_index == index or getattr(nearby_item, "label", None) == DocItemLabel.FORMULA:
                continue
            value = " ".join(str(getattr(nearby_item, "text", "") or "").split())
            if value:
                nearby_text.append(value)
        formulas.append({
            "text": text,
            "page": page,
            "context": " ".join(nearby_text),
        })
    return formulas


def _equation_record_text(formula, headings, equation_context, parent_text):
    heading_text = " > ".join(headings) if headings else ""
    parts = []
    if heading_text:
        parts.append(f"Section: {heading_text}")
    parts.append(f"Equation: {formula}")
    context = equation_context or parent_text
    if context:
        parts.append(f"Surrounding explanation: {context[:1500]}")
    return "\n".join(parts)


def _select_parent(formula, parents):
    same_page = [parent for parent in parents if parent.get("page") == formula.get("page")]
    candidates = same_page or parents
    if not candidates:
        return None
    context_terms = set(re.findall(r"[a-z0-9]+", formula.get("context", "").lower()))

    def overlap(parent):
        parent_terms = set(re.findall(r"[a-z0-9]+", parent.get("text", "").lower()))
        return len(context_terms & parent_terms)

    return max(candidates, key=overlap)


def chunk_docling_document(
    docling_document,
    source,
    title,
    equation_aware=False,
    chunker=None,
):
    chunker = chunker or create_docling_chunker()
    chunk_objects = list(chunker.chunk(docling_document))
    page_chunk_counts = {}
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

        signals = equation_signals(chunk_text)
        
        page_key = page_number if page_number is not None else "unknown"
        page_ordinal = page_chunk_counts.get(page_key, 0)
        page_chunk_counts[page_key] = page_ordinal + 1
        parent_record_key = (
            f"page_{page_key}_chunk_{page_ordinal}"
            if equation_aware
            else f"chunk_{chunk_index}"
        )
        chunks.append({
            "page": page_number,
            "chunk_index": chunk_index,
            "record_key": parent_record_key,
            "record_type": "context",
            "text": chunk_text.strip(),
            "source": str(source),
            "title": title,
            "headings": headings,
            "has_equation": signals["has_equation"],
            "equation_count": signals["equation_signal_count"],
            "ingestion_profile": "equation_aware" if equation_aware else "standard",
        })

    if equation_aware:
        parent_chunks = [chunk for chunk in chunks if chunk.get("record_type") == "context"]
        page_equation_counts = {}
        for equation_index, formula in enumerate(_document_formulas(docling_document)):
            parent = _select_parent(formula, parent_chunks)
            if parent is None:
                continue
            parent["has_equation"] = True
            parent["equation_count"] = int(parent.get("equation_count", 0)) + 1
            formula_page = formula["page"] if formula["page"] is not None else parent["page"]
            page_equation_ordinal = page_equation_counts.get(formula_page, 0)
            page_equation_counts[formula_page] = page_equation_ordinal + 1
            chunks.append({
                "page": formula_page,
                "chunk_index": parent["chunk_index"],
                "equation_index": equation_index,
                "record_key": f"page_{formula_page}_equation_{page_equation_ordinal}",
                "parent_record_key": parent["record_key"],
                "record_type": "equation",
                "text": _equation_record_text(
                    formula["text"],
                    parent["headings"],
                    formula["context"],
                    parent["text"],
                ),
                "equation_latex": formula["text"],
                "source": str(source),
                "title": title,
                "headings": parent["headings"],
                "has_equation": True,
                "equation_count": 1,
                "ingestion_profile": "equation_aware",
            })
    
    return chunks
