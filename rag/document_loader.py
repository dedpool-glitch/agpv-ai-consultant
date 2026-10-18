from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

def get_pdf_title(pdf_path):
    return Path(pdf_path).stem.replace('_', ' ')

def create_document_converter(equation_aware=False):
    if not equation_aware:
        return DocumentConverter()

    pipeline_options = PdfPipelineOptions(do_formula_enrichment=True)
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        }
    )


def load_pdf_document(pdf_path, equation_aware=False):
    pdf_path = Path(pdf_path)
    converter = create_document_converter(equation_aware=equation_aware)

    result = converter.convert(str(pdf_path))

    return {
        "docling_document": result.document,
        "title": get_pdf_title(pdf_path),
        "source": str(pdf_path),
    }

def load_pdfs_from_folder(folder_path, equation_aware=False):
    
    folder_path = Path(folder_path)
    documents = []

    for pdf_path in folder_path.glob("*.pdf"):
        document = load_pdf_document(pdf_path, equation_aware=equation_aware)
        documents.append(document)

    return documents
