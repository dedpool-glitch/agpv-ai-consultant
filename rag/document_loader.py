from pathlib import Path
from docling.document_converter import DocumentConverter

def get_pdf_title(pdf_path):
    return Path(pdf_path).stem.replace('_', ' ')

def load_pdf_document(pdf_path):
    pdf_path = Path(pdf_path)
    converter = DocumentConverter()

    result = converter.convert(str(pdf_path))

    return {
        "docling_document": result.document,
        "title": get_pdf_title(pdf_path),
        "source": str(pdf_path),
    }

def load_pdfs_from_folder(folder_path):
    
    folder_path = Path(folder_path)
    documents = []

    for pdf_path in folder_path.glob("*.pdf"):
        document = load_pdf_document(pdf_path)
        documents.append(document)

    return documents