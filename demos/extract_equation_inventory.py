"""Extract formula candidates and nearby context from PDFs with Docling.

Examples:
    python -m demos.extract_equation_inventory papers output.csv
    python -m demos.extract_equation_inventory books/alam_book.pdf output.csv --pages 120:150
"""

import argparse
import csv
from pathlib import Path

from docling_core.types.doc import DocItemLabel

from rag.document_loader import create_document_converter, get_pdf_title


FIELDS = [
    "source_type",
    "title",
    "source",
    "page",
    "equation",
    "context_before",
    "context_after",
    "suggested_question",
    "verification_status",
    "verification_notes",
]


def _pdf_paths(input_path):
    path = Path(input_path)
    if path.is_file() and path.suffix.lower() == ".pdf":
        return [path]
    if path.is_dir():
        return sorted(path.glob("*.pdf"))
    raise ValueError("Input must be a PDF or a folder containing PDFs.")


def _page(item):
    provenance = getattr(item, "prov", None) or []
    return provenance[0].page_no if provenance else ""


def _text(item):
    return " ".join(str(getattr(item, "text", "") or "").split())


def _context(items, index, direction, limit=2):
    selected = []
    cursor = index + direction
    while 0 <= cursor < len(items) and len(selected) < limit:
        item = items[cursor]
        if getattr(item, "label", None) != DocItemLabel.FORMULA:
            text = _text(item)
            if text:
                selected.append(text)
        cursor += direction
    if direction < 0:
        selected.reverse()
    return " ".join(selected)


def extract_from_pdf(converter, pdf_path, page_range=None, source_type=""):
    kwargs = {"page_range": page_range} if page_range else {}
    document = converter.convert(str(pdf_path), **kwargs).document
    items = [item for item, _level in document.iterate_items()]
    rows = []
    for index, item in enumerate(items):
        if getattr(item, "label", None) != DocItemLabel.FORMULA:
            continue
        equation = _text(item)
        if not equation:
            continue
        rows.append({
            "source_type": source_type,
            "title": get_pdf_title(pdf_path),
            "source": str(pdf_path),
            "page": _page(item),
            "equation": equation,
            "context_before": _context(items, index, -1),
            "context_after": _context(items, index, 1),
            "suggested_question": "",
            "verification_status": "needs_review",
            "verification_notes": "",
        })
    return rows


def _parse_pages(value):
    if not value:
        return None
    start, end = value.split(":", maxsplit=1)
    return int(start), int(end)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_path")
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--pages", help="Inclusive page range, for example 120:150")
    parser.add_argument("--source-type", choices=["papers", "books"], default="")
    parser.add_argument("--max-files", type=int)
    args = parser.parse_args()

    paths = _pdf_paths(args.input_path)
    if args.max_files is not None:
        paths = paths[: args.max_files]
    source_type = args.source_type or Path(args.input_path).parent.name
    page_range = _parse_pages(args.pages)
    converter = create_document_converter(equation_aware=True)

    rows = []
    for index, pdf_path in enumerate(paths, start=1):
        print(f"[{index}/{len(paths)}] Extracting equations from {pdf_path.name}")
        extracted = extract_from_pdf(
            converter,
            pdf_path,
            page_range=page_range,
            source_type=source_type,
        )
        print(f"  Found {len(extracted)} formula candidates")
        rows.extend(extracted)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} candidates to {args.output_csv}")


if __name__ == "__main__":
    main()
