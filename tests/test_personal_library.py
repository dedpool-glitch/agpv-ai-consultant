"""Personal PDFs persist locally and cannot cross library roots."""

from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
import pytest

from llm.rag_formatting import format_retrieved_context
from services.personal_library import (
    add_pdf, has_personal_documents, library_root, list_documents,
    remove_document, search_documents,
)


def text_pdf(text):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    resources = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})
    })
    page[NameObject("/Resources")] = resources
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_local_root_uses_windows_account_appdata(tmp_path, monkeypatch):
    monkeypatch.delenv("AGPV_PERSONAL_LIBRARY_ROOT", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert library_root() == tmp_path / "AgPV-Assistant" / "personal_library"


def test_upload_reopen_search_delete_and_separate_roots(tmp_path):
    first_root, second_root = tmp_path / "user-a", tmp_path / "user-b"
    pdf = text_pdf("Panel spacing influences light and crop yield")
    result = add_pdf("research.pdf", pdf, root=first_root)
    assert not result["already_present"]
    assert result["page_count"] == 1
    assert (first_root / "documents" / f"{result['document_id']}.pdf").read_bytes() == pdf
    assert has_personal_documents(first_root)
    assert add_pdf("same.pdf", pdf, root=first_root)["already_present"]
    assert len(list_documents(first_root)) == 1
    assert list_documents(second_root) == []
    assert search_documents("panel spacing", root=second_root) == []
    hits = search_documents("panel spacing", root=first_root)
    assert hits and hits[0]["metadata"]["library"] == "My library"
    assert "My library: research" in format_retrieved_context(hits)
    assert remove_document(result["document_id"], root=first_root)
    assert list_documents(first_root) == []
    assert not has_personal_documents(first_root)


def test_scanned_and_invalid_pdfs_do_not_enter_library(tmp_path):
    with pytest.raises(ValueError, match="PDF"):
        add_pdf("notes.txt", b"not a pdf", root=tmp_path)
    with pytest.raises(ValueError, match="searchable text"):
        buffer = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(buffer)
        add_pdf("blank.pdf", buffer.getvalue(), root=tmp_path)
    assert list_documents(tmp_path) == []
